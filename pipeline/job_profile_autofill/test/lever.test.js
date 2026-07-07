// Runs the REAL content/autofill.js against a simulated Lever apply form.
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

// Faithful to Lever's real markup: label is a separate .application-label,
// field is wrapped in .application-field, no for/id association.
const html = `<!DOCTYPE html><html><body>
  <form>
    <ul class="application-additional">
      <li class="application-question required">
        <label class="application-label">Current location <span class="required">✱</span></label>
        <div class="application-field"><input type="text" name="location" value="IND"></div>
      </li>

      <li class="application-question">
        <label class="application-label">Pronouns</label>
        <div class="application-field">
          <ul>
            <li><label><input type="checkbox" name="cards[uuid][field0][]" value="He/him">He/him</label></li>
            <li><label><input type="checkbox" name="cards[uuid][field0][]" value="She/her">She/her</label></li>
            <li><label><input type="checkbox" name="cards[uuid][field0][]" value="They/them">They/them</label></li>
            <li><label><input type="checkbox" name="cards[uuid][field0][]" value="Xe/xem">Xe/xem</label></li>
          </ul>
        </div>
      </li>

      <li class="application-question required">
        <label class="application-label">What is your working status in Spain? <span class="required">✱</span></label>
        <div class="application-field">
          <ul>
            <li><label><input type="radio" name="cards[uuid][field1]" value="European Union citizenship">European Union citizenship</label></li>
            <li><label><input type="radio" name="cards[uuid][field1]" value="European Union passport">European Union passport</label></li>
            <li><label><input type="radio" name="cards[uuid][field1]" value="Current work permit in Spain">Current work permit in Spain</label></li>
            <li><label><input type="radio" name="cards[uuid][field1]" value="Require work permit">Require work permit</label></li>
          </ul>
        </div>
      </li>

      <li class="application-question required">
        <label class="application-label">When would you be able to join us? <span class="required">✱</span></label>
        <div class="application-field"><textarea name="cards[uuid][field2]"></textarea></div>
      </li>

      <li class="application-question required">
        <label class="application-label">Are you willing to work on-site in Madrid (Spain)? <span class="required">✱</span></label>
        <div class="application-field"><textarea name="cards[uuid][field3]"></textarea></div>
      </li>

      <li class="application-question">
        <label class="application-label">What gender do you identify as?</label>
        <div class="application-field">
          <ul>
            <li><label><input type="radio" name="cards[uuid][field4]" value="Female">Female</label></li>
            <li><label><input type="radio" name="cards[uuid][field4]" value="Male">Male</label></li>
            <li><label><input type="radio" name="cards[uuid][field4]" value="Non-binary">Non-binary</label></li>
          </ul>
        </div>
      </li>
    </ul>
  </form>
</body></html>`;

const dom = new JSDOM(html, { url: "https://jobs.lever.co/skydance/x/apply", runScripts: "outside-only" });
const { window } = dom;

// expose browser globals the content script uses
global.window = window;
global.document = window.document;
global.CSS = window.CSS || { escape: (s) => s.replace(/[^a-zA-Z0-9_-]/g, "\\$&") };
global.HTMLInputElement = window.HTMLInputElement;
global.HTMLTextAreaElement = window.HTMLTextAreaElement;
global.HTMLSelectElement = window.HTMLSelectElement;
global.Event = window.Event;
global.File = window.File;
global.DataTransfer = window.DataTransfer;
global.getComputedStyle = window.getComputedStyle.bind(window);

// jsdom lacks layout: force getBoundingClientRect to report visible size
window.Element.prototype.getBoundingClientRect = function () {
  return { width: 100, height: 20, top: 0, left: 0, right: 100, bottom: 20 };
};
window.HTMLElement.prototype.scrollIntoView = function () {};

// load the real content script
const code = fs.readFileSync(path.join(__dirname, "..", "content", "autofill.js"), "utf8");
eval(code);

if (typeof window.__jobAutofillRun !== "function") { console.log("FAIL: content script did not expose __jobAutofillRun"); process.exit(1); }

const rules = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "config", "field-rules.json"), "utf8")).rules;
const profile = {
  firstName: "Sachin", lastName: "Desai", fullName: "Sachin Babaji Desai",
  email: "sachindesai7@gmail.com", phone: "+91-9820213275",
  location: "Bengaluru, India", pronouns: "He/Him", gender: "Male",
  linkedin: "https://linkedin.com/in/sachindesai7", portfolio: "https://sachindesai7.github.io",
  resume: null, coverLetter: null
};
const customQA = [
  { id: "qa-notice", question: "Notice", keywords: ["when would you be able to join","notice period","joining","availability"], answer: "I can join within 30 days of accepting an offer.", choice: "" },
  { id: "qa-work-auth", question: "Work auth", keywords: ["work permit","working status","visa","require work"], answer: "I am based in India...", choice: "Require work permit" },
  { id: "qa-reloc", question: "Relocation", keywords: ["relocat","on-site","willing to work on"], answer: "Yes. I am open to relocating and willing to work on-site anywhere.", choice: "Yes" }
];

const payload = { profile, customQA, rules };

window.__jobAutofillRun(payload).then((res) => {
  console.log("=== fill response ===");
  console.log(JSON.stringify(res, null, 2));
  console.log("\n=== resulting DOM state ===");
  const loc = document.querySelector('input[name="location"]');
  console.log("location value:", JSON.stringify(loc.value));
  const hehim = document.querySelector('input[value="He/him"]');
  console.log("He/him checked:", hehim.checked);
  const perm = document.querySelector('input[value="Require work permit"]');
  console.log("Require work permit checked:", perm.checked);
  const male = document.querySelector('input[value="Male"]');
  console.log("Male checked:", male.checked);
  const tas = document.querySelectorAll("textarea");
  console.log("join textarea:", JSON.stringify(tas[0].value));
  console.log("onsite textarea:", JSON.stringify(tas[1].value));
});

setTimeout(() => process.exit(0), 1500);
