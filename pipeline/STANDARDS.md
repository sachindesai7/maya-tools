# Maya Tool Development Standards

All tools in this repo follow these rules. No exceptions unless noted in the tool's spec file.

---

## 1. Folder and File Structure

Each tool lives in its own folder named after the tool. The folder contains the `.py` file and its icon.

```
maya-tools/
├── STANDARDS.md
├── CLAUDE.md
├── specs/
│   └── lod_generator.md        ← spec / ticket written before coding starts
└── tools/
    ├── lod_generator/
    │   ├── lod_generator.py    ← main tool file (same name as folder)
    │   ├── icon.png            ← 64x64 PNG shelf icon
    │   └── doc.md              ← design doc for this tool
    ├── foot_slider/
    │   ├── foot_slider.py
    │   ├── icon.png
    │   └── doc.md
    └── _tool_template/         ← copy this to start any new tool
        ├── _tool_template.py
        ├── icon.png
        └── doc.md
```

Rules:
- Every tool folder contains exactly three files: `tool_name.py`, `icon.png`, `doc.md`.
- Folder name = tool name = `.py` filename = `TOOL_NAME` value. All four must match.
- `doc.md` is the design document — written first, reviewed, then used to write the code.
- `icon.png` must be a 64×64 PNG. If missing, installer falls back to a Maya built-in icon.
- Shared utilities used by 3+ tools go in `tools/_utils/_utils.py`.
- One tool = one folder. No splitting logic across multiple files unless absolutely necessary.

---

## 2. Required Tool Metadata Block

Every tool file must start with this block immediately after the module docstring. These values drive the shelf button automatically.

```python
"""
Brief one-line description of what the tool does.
"""

# ── TOOL METADATA ─────────────────────────────────────────────────────────────
TOOL_NAME        = "lod_generator"          # matches filename without .py
TOOL_LABEL       = "LOD\nGen"               # shelf label, max 2 lines, keep short
TOOL_DESCRIPTION = "Generate LOD meshes from selected geometry with auto-naming"
TOOL_VERSION     = "1.0.0"
TOOL_AUTHOR      = "Sachin"
TOOL_ICON        = "icon.png"               # always icon.png, lives in the tool's own folder
SHELF_NAME       = "Pipeline"              # shelf tab to add button to
# ──────────────────────────────────────────────────────────────────────────────
```

`icon.png` must be a **64×64 PNG** placed in the tool's folder. If it is missing, the installer falls back to `pythonFamily.png` (Maya built-in).

When you don't have a custom icon yet, use one of these Maya built-in names as a temporary placeholder by setting `TOOL_ICON` to the name below instead of `"icon.png"`:
- `polyReduce.png` — LOD / mesh reduction tools
- `kinJoint.png` — rigging tools
- `ikHandle.png` — IK / foot slider tools
- `blendShape.png` — corrective shapes / blend shapes
- `pythonFamily.png` — generic Python tool
- `commandButton.png` — generic utility

Switch back to `"icon.png"` once you drop your custom icon into the folder.

---

## 3. Drop-In Shelf Button (REQUIRED IN EVERY TOOL)

Every tool **must** include these two functions verbatim at the bottom of the file. Maya calls `onMayaDroppedPythonFile` automatically when you drag the `.py` file into the Maya viewport.

```python
# ── SHELF INSTALLER ───────────────────────────────────────────────────────────

def _install_shelf_button():
    """Create or replace this tool's shelf button on the Pipeline shelf."""
    import maya.cmds as cmds
    import os

    # Get or create the target shelf
    main_shelf = mel.eval("$gShelfTopLevel = $gShelfTopLevel")
    shelves = cmds.tabLayout(main_shelf, query=True, childArray=True) or []
    shelf = None
    for s in shelves:
        if s == SHELF_NAME:        # shelf layout name IS the shelf identifier
            shelf = s
            break
    if shelf is None:
        shelf = cmds.shelfLayout(SHELF_NAME, parent=main_shelf)

    # Remove existing button with same label to avoid duplicates
    existing = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for btn in existing:
        if cmds.shelfButton(btn, query=True, label=True) == TOOL_LABEL:
            cmds.deleteUI(btn)

    # Resolve icon path (built-in name or repo-relative path)
    icon = TOOL_ICON
    if not os.path.isabs(icon) and not cmds.resourceString(icon):
        repo_root = os.path.dirname(os.path.abspath(__file__))
        icon = os.path.join(repo_root, icon)

    # Build the shelf button command
    cmd = "\n".join([
        f"import sys, os",
        f"_p = r'{os.path.dirname(os.path.abspath(__file__))}'",
        f"if _p not in sys.path: sys.path.insert(0, _p)",
        f"import {TOOL_NAME}",
        f"import importlib; importlib.reload({TOOL_NAME})",
        f"{TOOL_NAME}.show()",
    ])

    cmds.shelfButton(
        parent=shelf,
        label=TOOL_LABEL,
        annotation=TOOL_DESCRIPTION,
        command=cmd,
        image=icon,
        sourceType="python",
        style="iconAndTextVertical",
    )

    cmds.inViewMessage(
        assistMessage=f"<b>{TOOL_LABEL.replace(chr(10), ' ')}</b> added to <b>{SHELF_NAME}</b> shelf.",
        position="topCenter",
        fade=True,
    )


def onMayaDroppedPythonFile(*args, **kwargs):
    """Maya calls this automatically when the file is dragged into the viewport."""
    _install_shelf_button()

# ──────────────────────────────────────────────────────────────────────────────
```

---

## 4. Required `show()` Function

Every tool must expose a `show()` function. This is what the shelf button calls.

```python
def show():
    """Entry point. Called by shelf button and by other scripts."""
    # If the tool has a UI, open it here.
    # If the tool is headless, run it here and give feedback via inViewMessage.
    ui = MyToolUI()
    ui.show()
```

---

## 5. Tool Structure Order

Every file must follow this section order:

```
1. Module docstring
2. TOOL METADATA block
3. Imports (stdlib → maya.cmds → maya API → PySide2 → local)
4. Constants (if any beyond metadata)
5. Core logic functions
6. UI class (if tool has UI)
7. show() function
8. SHELF INSTALLER block (always last)
```

---

## 6. Dependencies and Requirements

If your tool depends on external Python packages (beyond Maya's built-in modules):

1. **Document them in `doc.md`** under a "Requirements" section:
   ```markdown
   ## Requirements
   - PySide2 (installed with Maya)
   - mcp>=1.0.0 (pip install mcp)
   - numpy (pip install numpy)
   ```

2. **Do NOT auto-install in the tool code.** Tools are drag-and-drop; installation should happen separately.

3. **For team tools:** Include a `requirements.txt` in the tool folder listing packages.
   ```
   tools/my_tool/
   ├── my_tool.py
   ├── icon.png
   ├── doc.md
   └── requirements.txt          ← list pip packages here
   ```

4. **For infrastructure tools** (like `maya_connector`), document setup in the `doc.md`:
   - What needs to be installed (`pip install mcp`)
   - When to install it (once per machine)
   - What it's used for (MCP server bridge)

**Example:** `tools/maya_connector/doc.md` says:
```
1. **Install the MCP server dependency** (once per machine):
   pip install mcp

2. **Drag `maya_connector.py` into the Maya viewport**
   ...
```

---

## 7. Maya API Usage

| Situation | Use |
|-----------|-----|
| Simple scene queries / basic commands | `maya.cmds` |
| Performance-critical loops (thousands of vertices/joints) | `maya.api.OpenMaya` (API 2.0) |
| Never use | `maya.OpenMaya` (API 1.0) — deprecated |

```python
# Good
import maya.cmds as cmds
import maya.api.OpenMaya as om   # API 2.0 only

# Bad
import maya.OpenMaya as om       # API 1.0, do not use
```

---

## 8. Undo Queue (REQUIRED)

Every tool action that modifies the scene must be wrapped in an undo chunk so the user can Ctrl+Z the entire operation as one step.

```python
def run_my_tool():
    cmds.undoInfo(openChunk=True, chunkName=TOOL_NAME)
    try:
        _do_the_work()
    except Exception as e:
        cmds.warning(f"[{TOOL_NAME}] Failed: {e}")
    finally:
        cmds.undoInfo(closeChunk=True)
```

Never leave chunks open. Always use try/finally.

---

## 9. Selection Validation

Always validate selection before doing anything. Give a clear in-viewport message, not just a script editor error.

```python
def _validate_selection(expected_type="mesh"):
    sel = cmds.ls(selection=True, dag=True, type=expected_type)
    if not sel:
        cmds.inViewMessage(
            assistMessage=f"<b>{TOOL_NAME}</b>: Select at least one <b>{expected_type}</b>.",
            position="topCenter",
            fade=True,
        )
        return None
    return sel
```

---

## 10. UI Standards (PySide2)

- Use **PySide2** only. Never PyQt5.
- UI class must inherit from `QtWidgets.QDialog`.
- Always parent to Maya's main window so the dialog doesn't fall behind.
- Window title format: `"Tool Name  v{TOOL_VERSION}"`
- **Never use `setFixedWidth`** — it clips text on different screen sizes/DPI. Use `setMinimumWidth` and let the layout expand to fit content.
- All labels and checkboxes must use `setWordWrap(True)` or `setMinimumWidth` large enough to show their full text without clipping.

```python
from PySide2 import QtWidgets, QtCore
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class MyToolUI(QtWidgets.QDialog):
    def __init__(self, parent=_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle(f"My Tool  v{TOOL_VERSION}")
        self.setMinimumWidth(320)                        # minimum, NOT fixed
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        # ... build your widgets here
```

Close any existing instance before opening a new one:

```python
def show():
    global _tool_window
    try:
        _tool_window.close()
        _tool_window.deleteLater()
    except Exception:
        pass
    _tool_window = MyToolUI()
    _tool_window.show()
```

---

## 11. Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| File | `snake_case.py` | `lod_generator.py` |
| Function | `snake_case` | `generate_lods()` |
| Class | `PascalCase` | `LodGeneratorUI` |
| Private function | `_leading_underscore` | `_build_lod_mesh()` |
| Constant | `UPPER_SNAKE` | `MAX_LOD_COUNT` |
| Maya node names | `descriptive_camelCase` | `footIK_handle`, `lod_geo_GRP` |

---

## 12. Logging and User Feedback

- **Never use `print()`** for user-facing messages.
- Use `cmds.warning()` for non-fatal issues (shows in script editor in orange).
- Use `cmds.inViewMessage()` for on-screen confirmations.
- Use `cmds.error()` only for unrecoverable failures (it raises an exception).

```python
# Good
cmds.warning(f"[{TOOL_NAME}] No mesh found, skipping.")
cmds.inViewMessage(assistMessage="LODs generated.", position="topCenter", fade=True)

# Bad
print("done")
```

---

## 13. Docstrings

Short, one-line docstrings only. No multi-paragraph essays.

```python
def generate_lods(mesh, count=3, reduction=0.5):
    """Generate LOD meshes from mesh at progressive reduction steps."""
```

No need to repeat what the function name already says. Only document non-obvious behavior.

---

## 14. No Hardcoded Paths

Every tool defines `_TOOL_DIR` at the top (after imports) and uses it for all paths.

```python
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

# Bad
icon_path = "C:/Users/Sachin/tools/lod_generator/icon.png"

# Good
icon_path = os.path.join(_TOOL_DIR, "icon.png")
```

---

## 15. Version Bump Rule

Bump `TOOL_VERSION` in the metadata block on every change:
- Bug fix → patch: `1.0.0 → 1.0.1`
- New feature → minor: `1.0.0 → 1.1.0`
- Breaking change → major: `1.0.0 → 2.0.0`

---

## 16. Checklist Before Committing

- [ ] `TOOL_NAME`, `TOOL_LABEL`, `TOOL_DESCRIPTION`, `TOOL_ICON` are filled in
- [ ] `onMayaDroppedPythonFile` is present and calls `_install_shelf_button()`
- [ ] `show()` function exists
- [ ] All scene modifications wrapped in undoInfo chunk with try/finally
- [ ] Selection validated with `inViewMessage` feedback
- [ ] No `print()` statements
- [ ] No hardcoded paths
- [ ] `TOOL_VERSION` bumped
- [ ] All external dependencies documented in `doc.md` under "Requirements"
- [ ] Tested by dragging `.py` into Maya viewport — shelf button appears
- [ ] Tested Ctrl+Z undoes the full operation
