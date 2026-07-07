# Job Profile Autofill

A Chrome extension (Manifest V3) that stores your job-application profile once and autofills application forms on any portal — Lever, Greenhouse, Workday, and others — with a single click.

> **Note:** Unlike the rest of `pipeline/`, this is a **browser extension**, not a Maya/Python shelf tool. The Maya `STANDARDS.md` / `CLAUDE.md` rules do not apply here. It lives in the pipeline folder as a general workflow-automation utility.

## What it does

- One popup to store your profile: name, email, phone, location, pronouns, gender, LinkedIn, portfolio.
- Resume + cover letter pulled from **Google Drive share links** (fetched once, cached as base64) or picked as local files.
- Custom **Q&A** with keyword matching — for free-text questions *and* radios/checkboxes/dropdowns (via an "exact option to pick" field).
- Click **⚡ Fill this page** on any application form → it scans every field, matches, and fills.

## How it works

| Piece | Role |
|---|---|
| `manifest.json` | MV3 manifest. Minimal perms: `storage`, `activeTab`, `scripting` + Google Drive hosts only. |
| `popup/` | Setup/edit UI + the "Fill this page" trigger. |
| `background.js` | Service worker — fetches Drive files (runs in the extension origin, so no CORS). |
| `content/autofill.js` | Injected on demand into every frame. Fingerprints each field (label, aria, placeholder, name, question container — with form-control text stripped), matches it against rules + Q&A, and fills it with a React-safe native setter. |
| `config/field-rules.json` | Editable regex patterns that map profile fields to form labels. |

### Field matching, briefly

For every `input` / `textarea` / `select`, a **fingerprint** is built from its label, ARIA attributes, placeholder, name/id, and its question container's label text (with nested `select`/`option`/`input` text removed so a dropdown's own options can't hijack the match). That fingerprint is tested against `config/field-rules.json`; first match wins. Radios, checkboxes, and dropdowns are matched to the option whose text best scores against the stored value. Custom Q&A uses the same mechanism keyed on your keywords.

## Privacy

- Profile data lives in `chrome.storage.local` on your machine.
- Only host permissions are `drive.google.com` — nothing else is read or sent.
- Resume/cover-letter Drive links must be shared "Anyone with the link". Those files (and the personal defaults seeded in `popup/popup.js`) are visible to anyone with this repo.

## Install & usage

See **[INSTALL.md](INSTALL.md)**.

## Development

```bash
npm install     # installs jsdom (dev only)
npm test        # runs the autofill logic against a simulated Lever form
```

`test/lever.test.js` loads the real `content/autofill.js` in jsdom against a faithful Lever DOM and asserts every field fills.

## Known limits

- Multi-page applications: click Fill on each page.
- Google-Places location autocompletes (Lever): the typed value is kept, but a stricter geocoder on some portals may clear it — verify before submit.
- Fields already holding your typed text are not overwritten (profile text fields overwrite only obvious junk that differs from your value).
- Always review a form before submitting — this is an assistant, not a guarantee.
