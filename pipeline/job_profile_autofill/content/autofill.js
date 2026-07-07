// Content script: scans the current page/frame for form fields, matches them
// against rules + custom Q&A, and fills them. Injected on demand by the popup.

(function () {

  // ---------- label fingerprint ----------

  function textOf(node) {
    return (node && node.textContent ? node.textContent : "").replace(/\s+/g, " ").trim();
  }

  // a container's label text WITHOUT the text of form controls it wraps —
  // stops a <select>'s own <option>s (LinkedIn, ArtStation, country names…)
  // from polluting the fingerprint and matching the wrong rule
  function containerLabelText(node) {
    if (!node) return "";
    const clone = node.cloneNode(true);
    clone.querySelectorAll("select, option, textarea, input, button").forEach((n) => n.remove());
    return textOf(clone);
  }

  function fingerprint(el) {
    const parts = [];

    // 1. <label for="...">
    if (el.id) {
      try {
        const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (label) parts.push(textOf(label));
      } catch (e) { /* invalid id for selector */ }
    }

    // 2. wrapping <label>
    const wrap = el.closest("label");
    if (wrap) parts.push(textOf(wrap));

    // 3. aria-label / aria-labelledby
    if (el.getAttribute("aria-label")) parts.push(el.getAttribute("aria-label"));
    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      labelledBy.split(/\s+/).forEach((id) => {
        const n = document.getElementById(id);
        if (n) parts.push(textOf(n));
      });
    }

    // 4. placeholder, name, id, autocomplete
    if (el.placeholder) parts.push(el.placeholder);
    if (el.name) parts.push(el.name);
    if (el.id) parts.push(el.id);
    if (el.getAttribute("autocomplete")) parts.push(el.getAttribute("autocomplete"));

    // 5. question context. Prefer a semantic question container (which holds the
    // label). Use ONLY its label text (controls stripped) so a select's options
    // don't leak in. Climb to preceding siblings ONLY when there is no semantic
    // container — otherwise a short-labeled field bleeds into the previous question.
    const semantic = el.closest('.application-question, fieldset, [role=group], [role=radiogroup]');
    if (semantic) {
      const t = containerLabelText(semantic);
      if (t && t.length < 300) parts.push(t);
    } else {
      const ctx = el.closest("li, td, section") || el.closest("div");
      if (ctx && ctx !== document.body) {
        let t = containerLabelText(ctx);
        let p = ctx.previousElementSibling, guard = 0;
        while (p && t.length < 40 && guard++ < 3) { t = containerLabelText(p) + " " + t; p = p.previousElementSibling; }
        if (t && t.length < 300) parts.push(t);
      }
    }

    return parts.join(" | ").toLowerCase();
  }

  // ---------- filling ----------

  function setNativeValue(el, value) {
    const proto =
      el instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : el instanceof HTMLSelectElement
          ? HTMLSelectElement.prototype
          : HTMLInputElement.prototype;
    const desc = Object.getOwnPropertyDescriptor(proto, "value");
    if (desc && desc.set) {
      desc.set.call(el, value); // bypasses React's wrapped setter
    } else {
      el.value = value;
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    // NOTE: intentionally no "blur" — it makes geocoder autocompletes (Lever's
    // location field) discard a typed value that wasn't picked from suggestions.
  }

  function norm(s) {
    return String(s).toLowerCase().replace(/[\s/_-]+/g, ""); // "He / Him" -> "hehim"
  }

  function fillSelect(el, value) {
    const target = String(value).toLowerCase();
    const targetN = norm(value);
    let match = null;
    for (const opt of el.options) {
      const optText = (opt.textContent || "").trim().toLowerCase();
      const optVal = (opt.value || "").toLowerCase();
      if (optText === target || optVal === target) { match = opt; break; }
      if (norm(optText) === targetN || norm(optVal) === targetN) { match = opt; break; }
      if (!match && optText && (optText.includes(target) || target.includes(optText))) match = opt;
    }
    if (!match) return false;
    setNativeValue(el, match.value);
    return true;
  }

  // an individual choice's own label — value + immediately-associated text only
  // (deliberately NOT the whole group container, or every option would look alike)
  function choiceOwnText(el) {
    let t = el.value || "";
    if (el.id) {
      try {
        const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (l) t += " " + textOf(l);
      } catch (e) { /* ignore */ }
    }
    const wrap = el.closest("label");
    if (wrap) t += " " + textOf(wrap);
    if (el.nextElementSibling) t += " " + textOf(el.nextElementSibling);
    if (el.previousElementSibling) t += " " + textOf(el.previousElementSibling);
    if (el.getAttribute("aria-label")) t += " " + el.getAttribute("aria-label");
    // fallback: the option row's own text (catches bare text-node labels),
    // only when short enough to be a single option and not the whole group
    const row = el.parentElement;
    if (row) {
      const rowText = textOf(row);
      if (rowText && rowText.length <= 40) t += " " + rowText;
    }
    return t;
  }

  function checkChoice(el) {
    if (!el.checked) el.click(); // click toggles a checkbox / selects a radio
    if (!el.checked) {            // fallback if the site intercepted the click
      el.checked = true;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  // score how well an option's text matches a target string (0 = no match)
  function optionScore(optText, target) {
    const optN = norm(optText);
    const targetN = norm(target);
    if (!optN || !targetN) return 0;
    if (optN === targetN) return 100;
    if (optN.includes(targetN) || targetN.includes(optN)) return 80;
    // word overlap fallback
    const optWords = optText.toLowerCase().match(/[a-z]{3,}/g) || [];
    const tgtWords = new Set(target.toLowerCase().match(/[a-z]{3,}/g) || []);
    if (!optWords.length) return 0;
    const shared = optWords.filter((w) => tgtWords.has(w)).length;
    return shared >= 2 || (shared === 1 && optWords.length <= 2) ? 40 + shared : 0;
  }

  // decide what value a group of choices should match, from profile rules then Q&A
  function targetForGroup(groupFp, rules, values, customQA) {
    for (const rule of rules) {
      if (rule.inputType === "file") continue;
      if (rule.patterns.some((p) => new RegExp(p, "i").test(groupFp)) && values[rule.field]) {
        return { label: rule.field, value: values[rule.field] };
      }
    }
    for (const qa of customQA) {
      const kws = (qa.keywords && qa.keywords.length ? qa.keywords : [qa.question]).filter(Boolean);
      if (kws.some((kw) => kw && groupFp.includes(kw.toLowerCase()))) {
        const pick = qa.choice || qa.answer;
        if (pick) return { label: "Q&A: " + qa.question, value: pick };
      }
    }
    return null;
  }

  // smallest element that contains every member of a group
  function commonAncestor(nodes) {
    if (nodes.length === 1) return nodes[0].parentElement || nodes[0];
    let a = nodes[0].parentElement;
    while (a && !nodes.every((n) => a.contains(n))) a = a.parentElement;
    return a || document.body;
  }

  // the question text for a group of choices — climbs to the question container
  // and pulls in a preceding label/legend if the container itself is thin
  function groupContext(members) {
    const box = commonAncestor(members);
    const q = box.closest && box.closest('.application-question, fieldset, [role=group], [role=radiogroup]');
    if (q) return textOf(q).toLowerCase(); // container already holds its own question label
    // no semantic container: pull in preceding siblings to find the label
    let txt = textOf(box);
    let p = box.previousElementSibling, guard = 0;
    while (p && txt.length < 60 && guard++ < 3) { txt = textOf(p) + " " + txt; p = p.previousElementSibling; }
    return txt.toLowerCase();
  }

  // radio + checkbox groups (pronouns, gender, work-status) — filled in a separate pass
  function fillRadioGroups(rules, values, customQA, report) {
    const inputs = document.querySelectorAll('input[type="radio"]:not([disabled]), input[type="checkbox"]:not([disabled])');
    const groups = {};
    for (const r of inputs) {
      const box = r.closest("fieldset, [role=radiogroup], [role=group]");
      const key = r.name || (box ? "grp-" + fingerprint(box) : "grp-" + fingerprint(r.parentElement));
      (groups[key] = groups[key] || []).push(r);
    }

    for (const key in groups) {
      const members = groups[key];
      const groupFp = groupContext(members);

      const target = targetForGroup(groupFp, rules, values, customQA);
      if (!target) continue;
      if (members.some((r) => r.checked)) { report.skipped.push(target.label + " (already selected)"); continue; }

      let best = null, bestScore = 0;
      for (const r of members) {
        const score = Math.max(optionScore(choiceOwnText(r), target.value), optionScore(r.value, target.value));
        if (score > bestScore) { bestScore = score; best = r; }
      }
      if (best && bestScore >= 40) {
        checkChoice(best);
        report.filled.push(target.label + (best.type === "checkbox" ? " (checkbox)" : " (radio)"));
      } else {
        report.skipped.push(target.label + " (no matching option)");
      }
    }
  }

  // react-select / custom dropdowns (div-based, not native <select>) — e.g. country of residence
  function sleep(ms) { return new Promise((res) => setTimeout(res, ms)); }

  async function fillComboboxes(rules, values, customQA, report) {
    // controls that look like a custom dropdown: role=combobox, or a container that shows "Select..."
    const candidates = new Set();
    document.querySelectorAll('[role="combobox"], [class*="select__control"], [class*="Select-control"], [class*="css-"][class*="control"]').forEach((c) => candidates.add(c));

    for (const control of candidates) {
      if (!isVisible(control)) continue;
      const box = control.closest("div, li, fieldset, section") || control;
      const context = textOf(box).toLowerCase();
      // skip if this context already handled as native/text elsewhere is hard to know; rely on target match
      const target = targetForGroup(context, rules, values, customQA);
      if (!target) continue;

      // already has a selected value? skip (heuristic: control text isn't just the placeholder)
      const controlText = textOf(control).toLowerCase();
      if (controlText && !/select\.\.\.|choose|^\s*$/.test(controlText) && controlText.length > 1) {
        report.skipped.push(target.label + " (dropdown already set)");
        continue;
      }

      try {
        control.scrollIntoView({ block: "center" });
        control.click(); // open the menu
        await sleep(250);

        // type into the inner input to filter, if present
        const input = control.querySelector('input') || document.querySelector('input[role="combobox"]');
        if (input) {
          setNativeValue(input, target.value);
          await sleep(350);
        }

        // find a matching option in the open listbox
        const options = document.querySelectorAll('[role="option"], [class*="select__option"], [class*="Select-option"], [id*="option"]');
        let best = null, bestScore = 0;
        for (const opt of options) {
          if (!isVisible(opt)) continue;
          const score = optionScore(textOf(opt), target.value);
          if (score > bestScore) { bestScore = score; best = opt; }
        }
        if (best && bestScore >= 40) {
          best.click();
          report.filled.push(target.label + " (dropdown)");
          await sleep(100);
        } else {
          report.skipped.push(target.label + " (dropdown: no option matched)");
          control.click(); // close menu
        }
      } catch (e) {
        report.skipped.push(target.label + " (dropdown error)");
      }
    }
  }

  function base64ToFile(b64, name, mime) {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new File([bytes], name, { type: mime });
  }

  function fillFileInput(el, fileData) {
    try {
      const file = base64ToFile(fileData.dataBase64, fileData.fileName, fileData.mimeType);
      const dt = new DataTransfer();
      dt.items.add(file);
      el.files = dt.files;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    } catch (e) {
      return false;
    }
  }

  // ---------- matching ----------

  function isVisible(el) {
    // file inputs are often intentionally hidden behind styled buttons — allow them
    if (el.type === "file") return true;
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function matchRule(el, fp, rules) {
    const isFile = el.type === "file";
    for (const rule of rules) {
      const ruleWantsFile = rule.inputType === "file";
      if (isFile !== ruleWantsFile) continue;
      if (rule.typeHint && el.type === rule.typeHint) {
        // type itself is strong signal (e.g. input type=email)
        return rule.field;
      }
      for (const p of rule.patterns) {
        if (new RegExp(p, "i").test(fp)) return rule.field;
      }
    }
    return null;
  }

  function matchQA(fp, customQA) {
    for (const qa of customQA) {
      const keywords = (qa.keywords && qa.keywords.length ? qa.keywords : [qa.question]).filter(Boolean);
      for (const kw of keywords) {
        if (kw && fp.includes(kw.toLowerCase())) return qa;
      }
    }
    return null;
  }

  // ---------- main ----------

  async function runFill(payload) {
    const { profile, customQA, rules } = payload;
    const report = { filled: [], skipped: [], unmatched: 0 };

    const values = {
      firstName: profile.firstName,
      lastName: profile.lastName,
      fullName: profile.fullName || [profile.firstName, profile.lastName].filter(Boolean).join(" "),
      email: profile.email,
      phone: profile.phone,
      location: profile.location,
      pronouns: profile.pronouns,
      gender: profile.gender,
      linkedin: profile.linkedin,
      portfolio: profile.portfolio
    };

    const elements = document.querySelectorAll(
      'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio]):not([type=password]), textarea, select'
    );

    for (const el of elements) {
      if (!isVisible(el) || el.disabled || el.readOnly) continue;
      // leave custom-dropdown internal inputs to the combobox pass
      if (el.getAttribute("role") === "combobox" ||
          el.closest('[class*="select__control"], [class*="Select-control"], [class*="select__value"]')) continue;

      const fp = fingerprint(el);
      if (!fp) { report.unmatched++; continue; }

      const field = matchRule(el, fp, rules);

      if (field === "resume" || field === "coverLetter") {
        const fileData = profile[field];
        if (fileData && fileData.dataBase64) {
          if (fillFileInput(el, fileData)) report.filled.push(field);
          else report.skipped.push(field + " (injection failed)");
        } else {
          report.skipped.push(field + " (no file stored)");
        }
        continue;
      }

      if (field && values[field]) {
        const cur = (el.value || "").trim();
        if (el instanceof HTMLSelectElement) {
          if (cur && norm(cur) === norm(values[field])) { report.skipped.push(field + " (already set)"); continue; }
          if (fillSelect(el, values[field])) report.filled.push(field);
          else report.skipped.push(field + " (no matching option)");
        } else {
          if (cur && norm(cur) === norm(values[field])) { report.skipped.push(field + " (already set)"); continue; }
          setNativeValue(el, values[field]);
          report.filled.push(field + (cur ? " (overwritten)" : ""));
        }
        continue;
      }

      // custom Q&A — text inputs, textareas, and native selects
      if (el.type !== "file") {
        const qa = matchQA(fp, customQA || []);
        if (qa) {
          if (el instanceof HTMLSelectElement) {
            const pick = qa.choice || qa.answer;
            if (pick && fillSelect(el, pick)) { report.filled.push("Q&A: " + qa.question); }
            else report.skipped.push("Q&A: " + qa.question + " (no matching option)");
            continue;
          }
          if (el.value && el.value.trim()) { report.skipped.push("Q&A: " + qa.question + " (already filled)"); continue; }
          if (qa.answer) { setNativeValue(el, qa.answer); report.filled.push("Q&A: " + qa.question); }
          continue;
        }
      }

      report.unmatched++;
    }

    fillRadioGroups(rules, values, customQA || [], report); // pronouns/gender/work-status radios & checkboxes
    await fillComboboxes(rules, values, customQA || [], report); // react-select style dropdowns (e.g. country)

    return report;
  }

  // Always (re)assign so re-injection picks up the latest code, even in a tab
  // that still has an older version loaded. Called directly via executeScript.
  window.__jobAutofillRun = function (payload) {
    return runFill(payload).then(
      (report) => ({ ok: true, report }),
      (e) => ({ ok: false, error: e.message })
    );
  };
})();
