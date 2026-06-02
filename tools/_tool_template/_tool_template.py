"""
One-line description of what this tool does.
"""

# ── TOOL METADATA ─────────────────────────────────────────────────────────────
TOOL_NAME        = "my_tool"
TOOL_LABEL       = "My\nTool"
TOOL_DESCRIPTION = "Describe what this tool does in one sentence."
TOOL_VERSION     = "1.0.0"
TOOL_AUTHOR      = "Sachin"
TOOL_ICON        = "icon.png"           # 64x64 PNG in this tool's folder (falls back to Maya built-in if missing)
SHELF_NAME       = "Pipeline"
# ──────────────────────────────────────────────────────────────────────────────

import os
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance

# Folder this file lives in — used for icon path and sys.path injection
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
# Add any tool-specific constants here
# ──────────────────────────────────────────────────────────────────────────────


# ── CORE LOGIC ────────────────────────────────────────────────────────────────

def _validate_selection(expected_type="mesh"):
    """Return selected nodes of expected_type or None with an in-viewport warning."""
    sel = cmds.ls(selection=True, dag=True, type=expected_type)
    if not sel:
        cmds.inViewMessage(
            assistMessage=f"<b>{TOOL_NAME}</b>: Select at least one <b>{expected_type}</b>.",
            position="topCenter",
            fade=True,
        )
        return None
    return sel


def run():
    """Main tool logic. Called by the UI's apply button."""
    sel = _validate_selection("mesh")
    if not sel:
        return

    cmds.undoInfo(openChunk=True, chunkName=TOOL_NAME)
    try:
        for mesh in sel:
            _process_mesh(mesh)
        cmds.inViewMessage(
            assistMessage=f"<b>{TOOL_NAME}</b>: Done.",
            position="topCenter",
            fade=True,
        )
    except Exception as e:
        cmds.warning(f"[{TOOL_NAME}] Failed: {e}")
    finally:
        cmds.undoInfo(closeChunk=True)


def _process_mesh(mesh):
    """Do the actual work on a single mesh node."""
    pass   # replace with real logic


# ── UI ────────────────────────────────────────────────────────────────────────

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class MyToolUI(QtWidgets.QDialog):
    def __init__(self, parent=_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle(f"My Tool  v{TOOL_VERSION}")
        self.setMinimumWidth(320)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)

        # ── add your widgets here ──
        self._apply_btn = QtWidgets.QPushButton("Apply")
        self._apply_btn.clicked.connect(run)
        layout.addWidget(self._apply_btn)

    def closeEvent(self, event):
        self.deleteLater()
        super().closeEvent(event)


_tool_window = None


def show():
    """Entry point — called by shelf button."""
    global _tool_window
    try:
        _tool_window.close()
        _tool_window.deleteLater()
    except Exception:
        pass
    _tool_window = MyToolUI()
    _tool_window.show()


# ── SHELF INSTALLER ───────────────────────────────────────────────────────────

def _install_shelf_button():
    """Create or replace this tool's shelf button on the Pipeline shelf."""
    main_shelf = mel.eval("$gShelfTopLevel = $gShelfTopLevel")
    shelves = cmds.tabLayout(main_shelf, query=True, childArray=True) or []

    shelf = None
    for s in shelves:
        if s == SHELF_NAME:
            shelf = s
            break
    if shelf is None:
        shelf = cmds.shelfLayout(SHELF_NAME, parent=main_shelf)

    # Remove duplicate buttons
    existing = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for btn in existing:
        try:
            if cmds.shelfButton(btn, query=True, label=True) == TOOL_LABEL:
                cmds.deleteUI(btn)
        except Exception:
            pass

    # Icon: use icon.png from tool folder; fall back to Maya built-in if missing
    icon_path = os.path.join(_TOOL_DIR, TOOL_ICON)
    icon = icon_path if os.path.isfile(icon_path) else "pythonFamily.png"

    cmd = "\n".join([
        "import sys",
        f"_p = r'{_TOOL_DIR}'",
        "if _p not in sys.path: sys.path.insert(0, _p)",
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
        assistMessage=f"<b>{TOOL_LABEL.replace(chr(10), ' ')}</b> added to <hl>{SHELF_NAME}</hl> shelf.",
        position="topCenter",
        fade=True,
    )


def onMayaDroppedPythonFile(*args, **kwargs):
    """Maya calls this automatically when the .py file is dragged into the viewport."""
    _install_shelf_button()

# ──────────────────────────────────────────────────────────────────────────────
