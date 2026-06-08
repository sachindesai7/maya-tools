# Figma Asset Exporter

A desktop tool to export images and videos from any **Figma** or **FigJam** board directly to a local folder — organised into subfolders by section.

Works with both the **Figma web app** (Chrome) and the **Figma desktop app**.

---

## Features

- Export **images** (PNG / JPG / WebP) in their original format
- Export **videos** (MP4 / MOV / WebM) in their original format
- Auto-organises exports into **subfolders per section/frame**
- **Live selection sync** via a companion Figma plugin — select nodes in Figma, click Send, only those assets get checked in the exporter
- **Filter bar** to quickly narrow assets by name or section
- Works on **FigJam boards** and **Figma design files**

---

## Requirements

- **Python 3.8+** — [Download here](https://www.python.org/downloads/)  
  ⚠️ During install, check **"Add Python to PATH"**
- **Figma account** (free or paid)
- Internet connection

> The app auto-installs the only external dependency (`requests`) on first launch.

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/figma-asset-exporter.git
cd figma-asset-exporter

# 2. Run setup (Windows)
setup.bat
```

Or just double-click **`run.bat`** — it installs dependencies and launches automatically.

---

## Getting a Figma API Token

1. Go to [figma.com](https://figma.com) in your browser
2. Click your avatar (top right) → **Settings**
3. **Security** tab → **Personal access tokens** → **Generate new token**
4. Set expiry to **30 days** or longer
5. Enable these scopes:
   - ✅ `file_content:read`
   - ✅ `file_metadata:read`
6. Copy the token — it's shown only once

---

## Usage

### Step 1 — Launch the app

```
run.bat
```

### Step 2 — Enter credentials

- Paste your **Personal Access Token**
- Paste your **Figma board URL**  
  Get it from: Figma → **Share** button → **Copy link**

### Step 3 — Fetch assets

Click **Fetch** — the app loads all images and videos from the board, grouped by section.

### Step 4 — Select what to export

**Option A — Filter by name:**  
Type in the Filter box → click **✓ Select Filtered** → export only matching assets

**Option B — Plugin (Figma Desktop App):**  
Select nodes directly in Figma and send them to the exporter (see Plugin Setup below)

**Option C — Manual:**  
Check/uncheck individual rows in the list

### Step 5 — Export

1. Click **Browse…** to choose an output folder
2. Click **Export Selected**
3. Files are saved into subfolders named after each Figma section

---

## Plugin Setup (Figma Desktop App)

The companion plugin lets you select images in Figma and sync the selection to the exporter with one click.

### Install once

1. Open your board in the **Figma desktop app**
2. Right-click on canvas → **Plugins** → **Development** → **Import plugin from manifest…**
3. Select `figma_plugin/manifest.json` from this folder
4. The plugin **"Asset Exporter Sync"** is now available

### Use every session

1. Make sure the **Figma Asset Exporter** app is running (it starts a local server on port 7788)
2. Fetch the board in the app first
3. In Figma — select the images/frames you want
4. Right-click → **Plugins** → **Development** → **Asset Exporter Sync**
5. Click **Send Selection to Exporter**
6. The app auto-checks only those assets
7. Click **Export Selected**

---

## File Structure

```
figma-asset-exporter/
├── figma_exporter.py          # Main application
├── figma_plugin/
│   ├── manifest.json          # Figma plugin manifest
│   ├── code.js                # Plugin logic
│   └── ui.html                # Plugin UI
├── requirements.txt           # Python dependencies
├── setup.bat                  # One-time setup (Windows)
├── run.bat                    # Launch app (Windows)
├── launch_chrome_debug.bat    # Optional: Chrome debug mode
└── README.md
```

---

## Output Structure

```
Your Output Folder/
├── Gameplay Screens/
│   ├── image_name.png
│   └── video_name.mp4
├── Key Art/
│   ├── hero_image.jpg
│   └── ...
└── UI Screens/
    └── ...
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `HTTP 403` on Fetch | Token expired or missing scopes — generate a new token |
| `HTTP 404` on Fetch | Wrong URL — use Share → Copy link from Figma |
| Videos not exporting | Known issue with some FigJam video fills — see Issues tab |
| Plugin not sending | Make sure the exporter app is open before clicking Send |
| Python not found | Re-install Python with "Add to PATH" checked |

---

## Contributing

PRs welcome. Open an issue for bugs or feature requests.

---

## License

MIT
