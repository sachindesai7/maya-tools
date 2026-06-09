# Figma Asset Exporter

Export images from Figma / FigJam boards directly to a local folder, auto-organised into subfolders by section and subsection — no API token required.

---

## How it works

| Component | Role |
|---|---|
| `figma_plugin/` | Figma plugin — runs inside Figma, reads image bytes, sends to server |
| `save_server.py` | Tiny local Python server — receives files and writes them to disk |

The plugin talks to `save_server.py` over `localhost:7788`. No cloud connection, no API token, no ZIP files.

---

## Output structure

```
Output Path/
  Section Name/
    Subsection Name/
      image_01.png
      image_02.jpg
      _download_video_here.txt   ← placeholder when video can't be auto-exported
```

---

## Setup (one-time)

1. Open Figma desktop or Figma web
2. Right-click canvas → **Plugins → Development → Import plugin from manifest…**
3. Select `figma_plugin/manifest.json`

Done — plugin loads as a development plugin, no further install needed.

---

## Usage (every session)

### Step 1 — Start the save server

Open a terminal in this folder:

```
python save_server.py
```

Leave the terminal open. You will see:
```
✅  Asset Exporter server — port 7788
    Leave this window open while exporting from Figma.
```

### Step 2 — Open the plugin

Right-click canvas → **Plugins → Development → Asset Exporter Sync**

### Step 3 — Export

1. Server status should show 🟢 **Server running on port 7788**
   - If 🔴 red, start `save_server.py` first then click **↻ Refresh**
2. Type your **output folder path** (e.g. `E:\Sachin\AI\exports`)
3. Select one or more **sections** in Figma
4. Click **⬇ Export to Folder**
5. Watch the progress — **✅ Finished!** when complete

---

## Multi-section export

Hold **Ctrl** or **Shift** and click multiple sections before exporting. Each section becomes its own top-level folder.

---

## Video files (FigJam)

FigJam embedded videos cannot be exported automatically — the Figma plugin API does not allow access to raw video bytes. When a video is detected:

- The correct folder is still created automatically
- A `_download_video_here.txt` placeholder is placed inside with instructions
- To get the actual video: **right-click the video node in Figma → Download**

---

## File structure

```
figma_exporter/
├── save_server.py          ← run this before exporting
├── .gitignore
├── README.md
└── figma_plugin/
    ├── manifest.json
    ├── code.js             ← plugin backend (runs inside Figma)
    └── ui.html             ← plugin UI
```

---

## Requirements

- **Python 3.x** — standard library only, no pip install needed
- **Figma desktop** or **Figma web** (latest version)
