// Popup: setup/edit UI + "fill this page" trigger.

const PROFILE_FIELDS = ["firstName", "lastName", "fullName", "email", "phone", "location", "pronouns", "gender", "linkedin", "portfolio"];
const DOCS = ["resume", "coverLetter"];

// bump this whenever the default Q&A set changes — forces a one-time re-sync
// of the built-in Q&As into already-saved profiles (user-added Q&As are kept).
const QA_VERSION = 2;

const DEFAULT_DATA = {
  profile: {
    firstName: "Sachin",
    lastName: "Desai",
    fullName: "Sachin Babaji Desai",
    email: "sachindesai7@gmail.com",
    phone: "+91-9820213275",
    location: "Bengaluru, India",
    pronouns: "He/Him",
    gender: "Male",
    linkedin: "https://linkedin.com/in/sachindesai7",
    portfolio: "https://sachindesai7.github.io",
    resume: {
      source: "gdrive",
      url: "https://drive.google.com/file/d/1nPYOHiCuUBSrxxkK37Cx63NP7Q3JEeXa/view?usp=drive_link",
      fileName: "Sachin_Desai_Resume.pdf",
      mimeType: "application/pdf",
      dataBase64: null
    },
    coverLetter: {
      source: "gdrive",
      url: "https://drive.google.com/file/d/1YKbkBgOtAnDSn58l-9DPuGSXjzUcDY0f/view?usp=drive_link",
      fileName: "Sachin_Desai_CoverLetter.pdf",
      mimeType: "application/pdf",
      dataBase64: null
    }
  },
  customQA: [
    {
      id: "qa-notice",
      question: "Notice period / when can you join",
      keywords: ["notice period", "when can you start", "when would you be able to join", "able to join", "join us", "when would you", "joining", "availability", "start date", "earliest you can", "how soon"],
      answer: "My notice period is 30 days, so I can join within 30 days of receiving a confirmed offer.",
      choice: ""
    },
    {
      id: "qa-work-auth",
      question: "Work authorization / permit status",
      keywords: ["work permit", "working status", "work authori", "authoriz", "visa", "sponsorship", "right to work", "eligible to work", "legally authorized", "require work"],
      answer: "I am based in India and do not require sponsorship to work in India. For roles located in other countries, I would require a work permit / visa sponsorship.",
      choice: "Require work permit"
    },
    {
      id: "qa-country-residence",
      question: "Country of residence",
      keywords: ["country of residence", "country you reside", "your country", "residence"],
      answer: "India",
      choice: "India"
    },
    {
      id: "qa-relocation",
      question: "Relocation / willingness to work on-site",
      keywords: ["relocat", "on-site", "onsite", "willing to work on", "willing to relocate", "open to relocat", "work from office", "move to"],
      answer: "Yes. I am open to relocating and willing to work on-site as required for the role, in any location.",
      choice: "Yes"
    },
    {
      id: "qa-source",
      question: "How did you hear about this position?",
      keywords: ["how did you hear", "hear about this", "hear about the", "referral source", "source"],
      answer: "LinkedIn",
      choice: "LinkedIn"
    }
  ]
};

let data = null;

// ---------- storage ----------

async function loadData() {
  const stored = await chrome.storage.local.get(["profile", "customQA", "qaVersion"]);
  if (stored.profile) {
    data = { profile: stored.profile, customQA: stored.customQA || [], qaVersion: stored.qaVersion || 0 };
    // migration: fill in fields added after this profile was saved
    if (data.profile.pronouns === undefined) data.profile.pronouns = DEFAULT_DATA.profile.pronouns;
    if (data.profile.gender === undefined) data.profile.gender = DEFAULT_DATA.profile.gender;
    if (!data.profile.location || data.profile.location === "India") data.profile.location = DEFAULT_DATA.profile.location;

    if (data.qaVersion < QA_VERSION) {
      // one-time re-sync: overwrite each built-in Q&A with the latest default
      // (keywords/answer/choice), keep any Q&A the user added themselves.
      const defById = new Map(DEFAULT_DATA.customQA.map((d) => [d.id, d]));
      const seen = new Set();
      data.customQA = data.customQA.map((qa) => {
        if (defById.has(qa.id)) { seen.add(qa.id); return structuredClone(defById.get(qa.id)); }
        return qa;
      });
      for (const def of DEFAULT_DATA.customQA) {
        if (!seen.has(def.id)) data.customQA.push(structuredClone(def));
      }
      data.qaVersion = QA_VERSION;
      await chrome.storage.local.set({ customQA: data.customQA, qaVersion: QA_VERSION });
    }

    // migration: seed Drive links into older saved profiles that lack them
    for (const doc of DOCS) {
      if (!data.profile[doc] || (!data.profile[doc].url && !data.profile[doc].dataBase64)) {
        data.profile[doc] = structuredClone(DEFAULT_DATA.profile[doc]);
      }
    }
  } else {
    data = structuredClone(DEFAULT_DATA); // first run: seed from resume
    data.qaVersion = QA_VERSION;
    await chrome.storage.local.set({ qaVersion: QA_VERSION });
  }
}

async function saveData() {
  collectFormIntoData();
  await chrome.storage.local.set(data);
  const s = document.getElementById("saveStatus");
  s.textContent = "Saved ✓";
  setTimeout(() => (s.textContent = ""), 2000);
}

// ---------- profile form ----------

function renderProfile() {
  for (const f of PROFILE_FIELDS) {
    document.getElementById(f).value = data.profile[f] || "";
  }
  for (const doc of DOCS) renderDocStatus(doc);
}

function collectFormIntoData() {
  for (const f of PROFILE_FIELDS) {
    data.profile[f] = document.getElementById(f).value.trim();
  }
  // Q&A collected live via input events; re-read to be safe
  data.customQA = [...document.querySelectorAll(".qa-item")].map((item, i) => ({
    id: item.dataset.id || `qa-${Date.now()}-${i}`,
    question: item.querySelector(".qa-question").value.trim(),
    keywords: item.querySelector(".qa-keywords").value.split(",").map((k) => k.trim()).filter(Boolean),
    answer: item.querySelector(".qa-answer").value.trim(),
    choice: item.querySelector(".qa-choice").value.trim()
  })).filter((qa) => qa.question || qa.answer || qa.choice);
}

// ---------- documents ----------

function renderDocStatus(doc) {
  const el = document.getElementById(doc + "Status");
  const d = data.profile[doc];
  el.classList.remove("stored", "error");
  if (d && d.dataBase64) {
    const kb = Math.round((d.dataBase64.length * 0.75) / 1024);
    const src = d.source === "gdrive" ? "Drive" : "local";
    el.textContent = `✓ ${d.fileName} (${kb} KB, ${src})`;
    el.classList.add("stored");
    if (d.source === "gdrive" && d.url) {
      document.getElementById(doc + "DriveUrl").value = d.url;
    }
  } else {
    el.textContent = "No file stored";
  }
}

function setDocError(doc, message) {
  const el = document.getElementById(doc + "Status");
  el.textContent = "✗ " + message;
  el.classList.remove("stored");
  el.classList.add("error");
}

function wireLocalFile(doc) {
  document.getElementById(doc + "File").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      data.profile[doc] = {
        source: "local",
        fileName: file.name,
        mimeType: file.type || "application/octet-stream",
        dataBase64: reader.result.split(",")[1]
      };
      renderDocStatus(doc);
    };
    reader.readAsDataURL(file);
  });
}

async function fetchDriveFor(doc, url) {
  const statusEl = document.getElementById(doc + "Status");
  statusEl.textContent = "Fetching from Drive…";
  statusEl.classList.remove("stored", "error");

  const res = await chrome.runtime.sendMessage({ type: "FETCH_DRIVE_FILE", url });
  if (!res || !res.ok) {
    setDocError(doc, (res && res.error) || "Fetch failed");
    return false;
  }
  const prev = data.profile[doc] || {};
  data.profile[doc] = {
    source: "gdrive",
    url,
    fileName: res.fileName || prev.fileName || (doc === "resume" ? "resume.pdf" : "cover-letter.pdf"),
    mimeType: res.mimeType === "application/octet-stream" ? (prev.mimeType || "application/pdf") : res.mimeType,
    dataBase64: res.base64,
    cachedAt: new Date().toISOString()
  };
  renderDocStatus(doc);
  return true;
}

function wireDriveFetch(doc) {
  document.getElementById(doc + "DriveFetch").addEventListener("click", async () => {
    const url = document.getElementById(doc + "DriveUrl").value.trim();
    if (!url) { setDocError(doc, "Paste a Drive link first"); return; }
    await fetchDriveFor(doc, url);
  });
}

// stored Drive link but no cached bytes yet → fetch + save automatically
async function autoFetchMissingDocs() {
  let fetched = false;
  for (const doc of DOCS) {
    const d = data.profile[doc];
    if (d && d.source === "gdrive" && d.url && !d.dataBase64) {
      if (await fetchDriveFor(doc, d.url)) fetched = true;
    }
  }
  if (fetched) await chrome.storage.local.set(data);
}

// ---------- custom Q&A ----------

function qaItemHTML(qa) {
  const div = document.createElement("div");
  div.className = "qa-item";
  div.dataset.id = qa.id || "";
  div.innerHTML = `
    <label>Question <input type="text" class="qa-question" /></label>
    <label>Match keywords (comma separated) <input type="text" class="qa-keywords" /></label>
    <label>Answer (for text boxes) <textarea class="qa-answer"></textarea></label>
    <label>Exact option to pick (for radio / checkbox / dropdown — optional) <input type="text" class="qa-choice" /></label>
    <button class="qa-remove">Remove</button>
  `;
  div.querySelector(".qa-question").value = qa.question || "";
  div.querySelector(".qa-keywords").value = (qa.keywords || []).join(", ");
  div.querySelector(".qa-answer").value = qa.answer || "";
  div.querySelector(".qa-choice").value = qa.choice || "";
  div.querySelector(".qa-remove").addEventListener("click", () => div.remove());
  return div;
}

function renderQA() {
  const list = document.getElementById("qaList");
  list.innerHTML = "";
  for (const qa of data.customQA) list.appendChild(qaItemHTML(qa));
}

// ---------- fill ----------

async function fillPage() {
  const reportEl = document.getElementById("fillReport");
  reportEl.classList.remove("hidden", "error");
  reportEl.textContent = "Filling…";

  try {
    collectFormIntoData();
    await chrome.storage.local.set(data);

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || /^(chrome|edge|about|chrome-extension):/.test(tab.url || "")) {
      throw new Error("This page cannot be filled (browser internal page).");
    }

    // 1) inject the (latest) content script into every frame
    await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      files: ["content/autofill.js"]
    });

    const rules = await (await fetch(chrome.runtime.getURL("config/field-rules.json"))).json();
    const payload = { profile: data.profile, customQA: data.customQA, rules: rules.rules };

    // 2) run the fill in every frame, collecting each frame's report
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      func: (p) => (window.__jobAutofillRun ? window.__jobAutofillRun(p) : null),
      args: [payload]
    });

    const totals = { filled: [], skipped: [], unmatched: 0 };
    for (const frame of results) {
      const res = frame && frame.result;
      if (res && res.ok) {
        totals.filled.push(...res.report.filled);
        totals.skipped.push(...res.report.skipped);
        totals.unmatched += res.report.unmatched;
      }
    }

    let text = `Filled ${totals.filled.length} field(s)`;
    if (totals.filled.length) text += `:\n  • ${totals.filled.join("\n  • ")}`;
    if (totals.skipped.length) text += `\nSkipped:\n  • ${totals.skipped.join("\n  • ")}`;
    if (!totals.filled.length && !totals.skipped.length) text = "No matching fields found on this page.";
    reportEl.textContent = text;
  } catch (e) {
    reportEl.textContent = "Error: " + e.message;
    reportEl.classList.add("error");
  }
}

// ---------- init ----------

document.addEventListener("DOMContentLoaded", async () => {
  await loadData();
  renderProfile();
  renderQA();

  for (const doc of DOCS) {
    wireLocalFile(doc);
    wireDriveFetch(doc);
  }

  document.getElementById("addQA").addEventListener("click", () => {
    document.getElementById("qaList").appendChild(qaItemHTML({ id: `qa-${Date.now()}` }));
  });

  document.getElementById("saveBtn").addEventListener("click", saveData);
  document.getElementById("fillBtn").addEventListener("click", fillPage);

  autoFetchMissingDocs(); // pulls resume/cover letter from stored Drive links on first open
});
