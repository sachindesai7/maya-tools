# Install & Usage

## 1. Get the files

Download or clone this folder (`pipeline/job_profile_autofill/`) to your machine. You need the folder that contains `manifest.json`.

## 2. Load in Chrome (developer mode)

1. Open Chrome → address bar → `chrome://extensions`
2. Turn **Developer mode** ON (top-right toggle)
3. Click **Load unpacked**
4. Select the `job_profile_autofill` folder (the one with `manifest.json`)
5. The card **Job Profile Autofill** appears. If it shows a red error, see Troubleshooting below.
6. Click the 🧩 puzzle icon in the toolbar → pin **Job Profile Autofill** so its icon stays visible.

> Works in any Chromium browser: Chrome, Edge, Brave. In Edge use `edge://extensions`.

## 3. Set up your profile

1. Click the extension icon — the popup opens with fields pre-seeded.
2. **Documents:** for resume and cover letter, either
   - pick a local file, **or**
   - paste a Google Drive **file** share link (`https://drive.google.com/file/d/FILE_ID/view`, shared "Anyone with the link") and click **Fetch**. It downloads once and caches; hit Fetch again after you update the file in Drive.
3. **Custom Q&A:** each entry has
   - **Keywords** (comma-separated) — matched against the form's question text.
   - **Answer** — typed into text boxes / textareas.
   - **Exact option to pick** (optional) — the option to select for radios, checkboxes, or dropdowns (e.g. `Require work permit`, `India`, `Yes`).
4. Click **💾 Save**.

## 4. Fill an application

1. Open a job application page (Lever/Greenhouse are the easiest to start with).
2. Click the extension icon → **⚡ Fill this page**.
3. A report lists what was filled and skipped. **Review the form before submitting.**

## Updating the extension after editing code

Edit files, then go to `chrome://extensions` and click the **↻ reload** icon on the extension card. No page reload is needed — the content script is re-injected fresh on each Fill. Popup-only edits (profile/Q&A) just need **Save**, no reload.

## Adding support for a stubborn portal

If a field doesn't fill, open `config/field-rules.json` and add a regex pattern to the relevant field's `patterns` array (case-insensitive), then reload the extension. For custom questions, add a Q&A entry in the popup with the right keywords.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "This page cannot be filled" | You're on a `chrome://` / extension page. Open an actual job form. |
| A dropdown stays empty | Its option label differs from your value — add/adjust the Q&A "exact option to pick". |
| Location field clears itself | It's a geocoder autocomplete on that portal; type/select manually. |
| Resume not attached after Fill | That portal blocks scripted uploads — attach manually (bytes are cached, no re-download). |
| Red error on the extension card | Open the card's "Errors", copy the message; usually a JSON/JS edit typo. |
