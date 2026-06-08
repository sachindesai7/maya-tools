import sys, subprocess

def _ensure_deps():
    try:
        import requests
    except ImportError:
        print("Installing 'requests'…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])

_ensure_deps()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import re
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

CDP_PORT    = 9222   # Chrome debug (optional)
PLUGIN_PORT = 7788   # Figma plugin sends selection here


class FigmaExporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Figma Asset Exporter")
        self.root.geometry("980x700")
        self.root.resizable(True, True)

        self.api_token = tk.StringVar()
        self.file_url  = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.nodes     = []
        self.checkboxes = {}
        self.file_key  = None
        self.headers   = {}
        self.media_map = {}

        self._build_ui()
        self._start_plugin_server()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 4}

        # Credentials
        cred = ttk.LabelFrame(self.root, text="Figma Credentials", padding=8)
        cred.pack(fill=tk.X, **pad)
        ttk.Label(cred, text="Personal Access Token:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(cred, textvariable=self.api_token, width=52, show="*").grid(row=0, column=1, padx=6, sticky=tk.EW)
        ttk.Button(cred, text="?", width=2, command=self._token_help).grid(row=0, column=2)

        ttk.Label(cred, text="Figma File / Board URL:").grid(row=1, column=0, sticky=tk.W, pady=(4, 0))
        ttk.Entry(cred, textvariable=self.file_url, width=52).grid(row=1, column=1, padx=6, sticky=tk.EW, pady=(4, 0))

        btn_frame = ttk.Frame(cred)
        btn_frame.grid(row=1, column=2, pady=(4, 0), padx=(0, 0))
        ttk.Button(btn_frame, text="📋 Clipboard", command=self._from_clipboard).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🌐 Chrome",    command=self._from_chrome).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Fetch",        command=self._fetch_assets).pack(side=tk.LEFT, padx=2)

        cred.columnconfigure(1, weight=1)

        # Output folder
        out = ttk.Frame(self.root)
        out.pack(fill=tk.X, **pad)
        ttk.Label(out, text="Output Folder:").pack(side=tk.LEFT)
        ttk.Entry(out, textvariable=self.output_folder, width=55).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
        ttk.Button(out, text="Browse…", command=self._browse_folder).pack(side=tk.LEFT)

        # Chrome tip label
        self.chrome_tip = tk.StringVar(value="Tip: select a node in Figma → click 🌐 Chrome to auto-read URL  |  Or copy Figma URL → 📋 Clipboard")
        ttk.Label(self.root, textvariable=self.chrome_tip, foreground="#555", font=("", 8)).pack(anchor="w", padx=12)

        # Filter bar
        fbar = ttk.Frame(self.root)
        fbar.pack(fill=tk.X, padx=10, pady=(2, 0))
        ttk.Label(fbar, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(fbar, textvariable=self.filter_var, width=30).pack(side=tk.LEFT, padx=6)
        ttk.Button(fbar, text="✓ Select Filtered",   command=self._select_filtered).pack(side=tk.LEFT, padx=2)
        ttk.Button(fbar, text="✗ Deselect Filtered", command=self._deselect_filtered).pack(side=tk.LEFT, padx=2)
        ttk.Button(fbar, text="Clear",               command=lambda: self.filter_var.set("")).pack(side=tk.LEFT, padx=2)
        self.count_var = tk.StringVar(value="")
        ttk.Label(fbar, textvariable=self.count_var, foreground="#555").pack(side=tk.LEFT, padx=8)

        # Asset list
        list_frame = ttk.LabelFrame(self.root, text="Assets — check to export", padding=6)
        list_frame.pack(fill=tk.BOTH, expand=True, **pad)

        cols = ("sel", "section", "name", "type", "node_id")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="none")
        self.tree.heading("sel",     text="✓")
        self.tree.heading("section", text="Section / Frame")
        self.tree.heading("name",    text="Asset Name")
        self.tree.heading("type",    text="Type")
        self.tree.heading("node_id", text="Node ID")
        self.tree.column("sel",     width=30,  stretch=False, anchor="center")
        self.tree.column("section", width=230)
        self.tree.column("name",    width=230)
        self.tree.column("type",    width=70,  anchor="center")
        self.tree.column("node_id", width=140)

        vsb = ttk.Scrollbar(list_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.tree.bind("<Button-1>", self._toggle_row)

        bot = ttk.Frame(self.root)
        bot.pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(bot, text="Select All",      command=self._select_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(bot, text="Deselect All",    command=self._deselect_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(bot, text="Export Selected", command=self._export).pack(side=tk.RIGHT, padx=4)

        self.status_var = tk.StringVar(value="Plugin server listening on :7788 — select images in Figma, run plugin, click Send.")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(fill=tk.X, padx=10)
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 6))

    # ── Figma Plugin server ───────────────────────────────────────────────────

    def _start_plugin_server(self):
        """HTTP server on localhost:7788 — receives selection from Figma plugin."""
        app = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass   # silence request logs

            def do_OPTIONS(self):
                # Preflight CORS for the plugin iframe
                self.send_response(200)
                self._cors()
                self.end_headers()

            def do_POST(self):
                if self.path != "/selection":
                    self.send_response(404); self.end_headers(); return
                length = int(self.headers.get("Content-Length", 0))
                body   = self.rfile.read(length)
                try:
                    data  = json.loads(body)
                    nodes = data.get("nodes", [])
                    app.root.after(0, lambda n=nodes: app._apply_plugin_selection(n))
                    self.send_response(200)
                    self._cors()
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"ok":true}')
                except Exception as e:
                    self.send_response(400); self.end_headers()

            def _cors(self):
                self.send_header("Access-Control-Allow-Origin",  "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def run():
            try:
                srv = HTTPServer(("localhost", PLUGIN_PORT), Handler)
                srv.serve_forever()
            except Exception:
                pass   # port in use — silently skip

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def _apply_plugin_selection(self, nodes):
        """Called on main thread when plugin sends selection."""
        if not nodes:
            self._set_status("Plugin: nothing selected in Figma.")
            return

        node_ids = {n["id"] for n in nodes}

        # Check if we've already fetched these nodes' assets
        matched = [r for r in self.tree.get_children()
                   if self.tree.set(r, "node_id") in node_ids]

        if matched:
            # Deselect all, then check only the plugin-selected ones
            for row in self.tree.get_children():
                self.checkboxes[row] = False
                self.tree.set(row, "sel", "☐")
            for row in matched:
                self.checkboxes[row] = True
                self.tree.set(row, "sel", "☑")
            self._set_status(
                f"Plugin: {len(matched)} asset(s) matched from Figma selection. Ready to export."
            )
        else:
            # Assets not yet fetched — store node IDs and try to fetch
            names = ", ".join(n["name"] for n in nodes[:5])
            self._set_status(
                f"Plugin: received {len(nodes)} node(s) ({names}…). "
                f"Fetch the board first, or the selection is outside current scope."
            )

    # ── Chrome / Clipboard URL sync ──────────────────────────────────────────

    def _from_chrome(self):
        """Read current Figma tab URL via Chrome DevTools Protocol (port 9222)."""
        try:
            tabs = requests.get(f"http://localhost:{CDP_PORT}/json", timeout=2).json()
        except Exception:
            messagebox.showinfo(
                "Chrome not in debug mode",
                "Chrome must be started with:\n"
                "  --remote-debugging-port=9222\n\n"
                "Use the included  launch_chrome_debug.bat  file.\n"
                "Close Chrome first, then run the bat, then try again."
            )
            return

        figma_url = None
        for tab in tabs:
            url = tab.get("url", "")
            if "figma.com" in url:
                figma_url = url
                break

        if not figma_url:
            messagebox.showwarning("No Figma tab", "No Figma tab found in Chrome.")
            return

        self.file_url.set(figma_url)
        node_id = self._extract_node_id(figma_url)
        if node_id:
            self._set_status(f"Read from Chrome — node {node_id}. Fetching…")
        else:
            self._set_status("Read from Chrome — no node selected (click a node in Figma first). Fetching full board…")
        self._fetch_assets()

    def _from_clipboard(self):
        """Read Figma URL from clipboard."""
        try:
            text = self.root.clipboard_get().strip()
        except Exception:
            messagebox.showwarning("Clipboard empty", "Nothing in clipboard.")
            return

        if "figma.com" not in text:
            messagebox.showwarning("Not a Figma URL", "Clipboard doesn't contain a figma.com URL.")
            return

        self.file_url.set(text)
        self._set_status("URL pasted from clipboard. Fetching…")
        self._fetch_assets()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _token_help(self):
        messagebox.showinfo(
            "How to get a Figma token",
            "1. figma.com → account Settings\n"
            "2. Security tab → Personal access tokens\n"
            "3. Generate token — check:\n"
            "     file_content:read\n"
            "     file_metadata:read\n"
            "4. Copy and paste here."
        )

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)

    def _extract_file_key(self, url):
        m = re.search(r'figma\.com/(?:file|design|board|proto)/([A-Za-z0-9_-]+)', url)
        return m.group(1) if m else None

    def _extract_node_id(self, url):
        """node-id in URL: X-Y format → API wants X:Y."""
        params = parse_qs(urlparse(url).query)
        raw = params.get("node-id", [None])[0]
        return raw.replace("-", ":") if raw else None

    def _safe_name(self, name):
        return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip() or "unnamed"

    def _unique_path(self, folder, base, ext):
        path = os.path.join(folder, f"{base}.{ext}")
        n = 1
        while os.path.exists(path):
            path = os.path.join(folder, f"{base}_{n}.{ext}")
            n += 1
        return path

    def _set_status(self, msg):
        self.root.after(0, lambda: self.status_var.set(msg))

    # ── Filter ───────────────────────────────────────────────────────────────

    def _visible_rows(self):
        return self.tree.get_children()

    def _filtered_rows(self):
        q = self.filter_var.get().strip().lower()
        if not q:
            return list(self._visible_rows())
        return [
            row for row in self._visible_rows()
            if q in self.tree.set(row, "name").lower()
            or q in self.tree.set(row, "section").lower()
        ]

    def _apply_filter(self):
        q = self.filter_var.get().strip().lower()
        all_rows = self.tree.get_children()
        if not q:
            for row in all_rows:
                self.tree.reattach(row, "", "end")
            self.count_var.set("")
            return
        visible = []
        for row in all_rows:
            name    = self.tree.set(row, "name").lower()
            section = self.tree.set(row, "section").lower()
            if q in name or q in section:
                self.tree.reattach(row, "", "end")
                visible.append(row)
            else:
                self.tree.detach(row)
        self.count_var.set(f"{len(visible)} shown")

    def _select_filtered(self):
        for row in self._filtered_rows():
            self.checkboxes[row] = True
            self.tree.set(row, "sel", "☑")

    def _deselect_filtered(self):
        for row in self._filtered_rows():
            self.checkboxes[row] = False
            self.tree.set(row, "sel", "☐")

    # ── Tree checkbox ─────────────────────────────────────────────────────────

    def _toggle_row(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            new = not self.checkboxes.get(row, False)
            self.checkboxes[row] = new
            self.tree.set(row, "sel", "☑" if new else "☐")

    def _select_all(self):
        for row in self._visible_rows():
            self.checkboxes[row] = True
            self.tree.set(row, "sel", "☑")

    def _deselect_all(self):
        for row in self._visible_rows():
            self.checkboxes[row] = False
            self.tree.set(row, "sel", "☐")

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def _fetch_assets(self):
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        token = self.api_token.get().strip()
        url   = self.file_url.get().strip()
        if not token or not url:
            messagebox.showerror("Missing", "Enter token and file URL.")
            return

        file_key = self._extract_file_key(url)
        if not file_key:
            messagebox.showerror("Bad URL", "Could not extract file key from URL.")
            return

        node_id = self._extract_node_id(url)
        headers = {"X-Figma-Token": token}
        self._set_status("Fetching file structure…")

        try:
            # Always fetch full file — /nodes endpoint is unreliable on FigJam boards.
            r = requests.get(f"https://api.figma.com/v1/files/{file_key}",
                              headers=headers, timeout=60)
            r.raise_for_status()
            full_doc  = r.json().get("document", {})

            if node_id:
                # Scope walk to the specific node visible in Figma tab.
                target = self._find_node(full_doc, node_id)
                if target:
                    root_node     = target
                    section_depth = 1
                else:
                    root_node     = full_doc
                    section_depth = 2
            else:
                root_node     = full_doc
                section_depth = 2
        except requests.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            if code == 403:
                msg = "Access denied (403) — check token scopes:\n  file_content:read\n  file_metadata:read"
            elif code == 404:
                msg = "File not found (404) — check the URL."
            else:
                body = (e.response.text[:300] if e.response else "no response")
                msg  = f"HTTP {code}:\n{body}"
            messagebox.showerror("Fetch error", msg)
            self._set_status("Error.")
            return
        except Exception as e:
            messagebox.showerror("Fetch error", f"{type(e).__name__}: {e}")
            self._set_status("Error.")
            return

        # Media fills → CDN download URLs
        try:
            mr = requests.get(f"https://api.figma.com/v1/files/{file_key}/images",
                               headers=headers, timeout=20)
            mr.raise_for_status()
            self.media_map = mr.json().get("meta", {}).get("images", {})
        except Exception:
            self.media_map = {}

        self.file_key = file_key
        self.headers  = headers
        self.nodes    = []
        self._walk(root_node, depth=0, section=None, section_depth=section_depth)

        self._set_status(f"Found {len(self.nodes)} asset(s). Select and click Export.")
        self.root.after(0, self._populate_tree)

    def _walk(self, node, depth, section, section_depth):
        node_type = node.get("type", "")
        name      = node.get("name", "unnamed")

        if node_type == "SECTION" or depth == section_depth:
            section = name

        for fill in node.get("fills", []):
            ftype = fill.get("type", "")
            if ftype in ("IMAGE", "VIDEO"):
                # VIDEO fills may use imageRef, videoHash, or hash — try all
                ref = (fill.get("imageRef") or
                       fill.get("videoHash") or
                       fill.get("hash") or "")
                self.nodes.append({
                    "id":        node.get("id", ""),
                    "name":      name,
                    "type":      "video" if ftype == "VIDEO" else "image",
                    "image_ref": ref,
                    "fill_keys": list(fill.keys()),   # for diagnostics
                    "section":   section or "Unsorted",
                })
                break

        for child in node.get("children", []):
            self._walk(child, depth + 1, section, section_depth)

    def _find_node(self, node, target_id):
        """DFS search for a node by ID."""
        if node.get("id") == target_id:
            return node
        for child in node.get("children", []):
            result = self._find_node(child, target_id)
            if result:
                return result
        return None

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.checkboxes.clear()
        self.filter_var.set("")
        self.count_var.set("")
        for node in self.nodes:
            row = self.tree.insert("", "end", values=(
                "☑", node["section"], node["name"], node["type"].upper(), node["id"],
            ))
            self.checkboxes[row] = True

    # ── Export ────────────────────────────────────────────────────────────────

    def _export(self):
        if not self.output_folder.get().strip():
            messagebox.showerror("No folder", "Select an output folder first.")
            return
        if not self.file_key:
            messagebox.showerror("Not ready", "Fetch assets first.")
            return
        threading.Thread(target=self._export_thread, daemon=True).start()

    def _export_thread(self):
        folder   = self.output_folder.get().strip()
        all_rows = self.tree.get_children()
        selected = [
            self.nodes[i]
            for i, row in enumerate(all_rows)
            if self.checkboxes.get(row, False)
        ]
        if not selected:
            messagebox.showwarning("Nothing selected", "Check at least one asset.")
            return

        os.makedirs(folder, exist_ok=True)
        total = len(selected)
        done  = 0
        self.root.after(0, lambda: self.progress.configure(maximum=total, value=0))

        for node in selected:
            ref    = node.get("image_ref", "")
            dl_url = self.media_map.get(ref)
            if not dl_url:
                fill_keys = node.get("fill_keys", [])
                messagebox.showwarning(
                    "Warning",
                    f"No CDN URL for: {node['name']} ({node['type']})\n"
                    f"image_ref: {ref or '(empty)'}\n"
                    f"Fill keys: {fill_keys}\n"
                    f"media_map has {len(self.media_map)} entries\n"
                    f"Ref in map: {ref in self.media_map}"
                )
                done += 1
                self.root.after(0, lambda d=done: self.progress.configure(value=d))
                continue

            self._set_status(f"Downloading {node['type']}: {node['name']}…")
            try:
                vr = requests.get(dl_url, stream=True, timeout=120)
                vr.raise_for_status()
                ct = vr.headers.get("Content-Type", "")

                if node["type"] == "image":
                    ext = _ext_from_content_type_image(ct) or _ext_from_url(dl_url) or "png"
                else:
                    ext = _ext_from_content_type_video(ct) or _ext_from_url(dl_url) or "mp4"

                sec_dir = os.path.join(folder, self._safe_name(node["section"]))
                os.makedirs(sec_dir, exist_ok=True)
                path = self._unique_path(sec_dir, self._safe_name(node["name"]), ext)
                with open(path, "wb") as f:
                    for chunk in vr.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
            except Exception as e:
                messagebox.showerror("Export error", f"Download failed for {node['name']}:\n{e}")

            done += 1
            self.root.after(0, lambda d=done: self.progress.configure(value=d))
            self._set_status(f"Exported {done}/{total}…")

        self._set_status(f"Done — {done} asset(s) saved to: {folder}")
        messagebox.showinfo("Export complete", f"Saved {done} asset(s) to:\n{folder}")


# ── Utilities ────────────────────────────────────────────────────────────────

def _ext_from_content_type_image(ct):
    ct = ct.lower()
    if "png"  in ct: return "png"
    if "jpeg" in ct: return "jpg"
    if "jpg"  in ct: return "jpg"
    if "gif"  in ct: return "gif"
    if "webp" in ct: return "webp"
    if "svg"  in ct: return "svg"
    return None

def _ext_from_content_type_video(ct):
    ct = ct.lower()
    if "webm"      in ct: return "webm"
    if "quicktime" in ct: return "mov"
    if "mp4"       in ct: return "mp4"
    if "gif"       in ct: return "gif"
    if "ogg"       in ct: return "ogv"
    if "avi"       in ct: return "avi"
    return None

def _ext_from_url(url):
    path = url.split("?")[0].split("/")[-1]
    if "." in path:
        return path.rsplit(".", 1)[-1].lower()
    return None


# ── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app  = FigmaExporter(root)
    root.mainloop()
