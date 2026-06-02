"""
Maya MCP Connector — opens Maya's command port so Claude Code can talk to Maya.
Drag this file into the Maya viewport to install a shelf button.
"""

# ── TOOL METADATA ─────────────────────────────────────────────────────────────
TOOL_NAME        = "maya_connector"
TOOL_LABEL       = "MCP\nPort"
TOOL_DESCRIPTION = "Start/stop the Maya command port so Claude Code can connect"
TOOL_VERSION     = "1.0.0"
TOOL_AUTHOR      = "Sachin"
TOOL_ICON        = "icon.png"
SHELF_NAME       = "Pipeline"
MCP_PORT         = 7001
# ──────────────────────────────────────────────────────────────────────────────

import os
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance

_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Core logic ────────────────────────────────────────────────────────────────

def is_port_open(port=MCP_PORT):
    """Return True if the command port is currently open."""
    try:
        return bool(cmds.commandPort(f":{port}", query=True))
    except Exception:
        return False


def open_port(port=MCP_PORT):
    """Open Maya's command port for Claude Code."""
    port_str = f":{port}"
    try:
        if cmds.commandPort(port_str, query=True):
            cmds.commandPort(port_str, close=True)
    except Exception:
        pass
    cmds.commandPort(name=port_str, sourceType="python", echoOutput=False, noreturn=False)
    cmds.inViewMessage(
        assistMessage=f"<b>MCP Port {port}</b> is <hl>open</hl>. Claude Code can connect.",
        position="topCenter", fade=True,
    )


def close_port(port=MCP_PORT):
    """Close the command port."""
    port_str = f":{port}"
    try:
        if cmds.commandPort(port_str, query=True):
            cmds.commandPort(port_str, close=True)
        cmds.inViewMessage(
            assistMessage=f"<b>MCP Port {port}</b> closed.",
            position="topCenter", fade=True,
        )
    except Exception as e:
        cmds.warning(f"[maya_connector] Could not close port: {e}")


# ── UI ────────────────────────────────────────────────────────────────────────

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class MayaConnectorUI(QtWidgets.QDialog):
    def __init__(self, parent=_maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle(f"Maya MCP Connector  v{TOOL_VERSION}")
        self.setMinimumWidth(320)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build_ui()
        self._refresh()

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)  # poll every 2s

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Status row
        status_row = QtWidgets.QHBoxLayout()
        self._status_dot = QtWidgets.QLabel("●")
        self._status_dot.setFixedWidth(18)
        self._status_label = QtWidgets.QLabel("Checking...")
        status_row.addWidget(self._status_dot)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Port field
        port_row = QtWidgets.QHBoxLayout()
        port_row.addWidget(QtWidgets.QLabel("Port:"))
        self._port_spin = QtWidgets.QSpinBox()
        self._port_spin.setRange(1024, 65535)
        self._port_spin.setValue(MCP_PORT)
        self._port_spin.setFixedWidth(80)
        port_row.addWidget(self._port_spin)
        port_row.addStretch()
        layout.addLayout(port_row)

        # Toggle button
        self._toggle_btn = QtWidgets.QPushButton("Start Port")
        self._toggle_btn.setFixedHeight(36)
        self._toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self._toggle_btn)

        # Info label
        info = QtWidgets.QLabel(
            "Once the port is open, Claude Code can connect. "
            "Keep this port open while using Claude Code."
        )
        info.setWordWrap(True)
        info.setMinimumWidth(300)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # Auto-start checkbox
        self._auto_cb = QtWidgets.QCheckBox("Auto-start port when Maya launches")
        self._auto_cb.setMinimumWidth(300)
        self._auto_cb.stateChanged.connect(self._toggle_auto_start)
        layout.addWidget(self._auto_cb)
        self._check_auto_start()

    def _refresh(self):
        open_ = is_port_open(self._port_spin.value())
        if open_:
            self._status_dot.setStyleSheet("color: #4CAF50; font-size: 16px;")
            self._status_label.setText(f"Port {self._port_spin.value()} is OPEN")
            self._toggle_btn.setText("Stop Port")
            self._toggle_btn.setStyleSheet("background-color: #c0392b; color: white;")
        else:
            self._status_dot.setStyleSheet("color: #888; font-size: 16px;")
            self._status_label.setText(f"Port {self._port_spin.value()} is closed")
            self._toggle_btn.setText("Start Port")
            self._toggle_btn.setStyleSheet("background-color: #27ae60; color: white;")

    def _toggle(self):
        port = self._port_spin.value()
        if is_port_open(port):
            close_port(port)
        else:
            open_port(port)
        self._refresh()

    def _check_auto_start(self):
        """Check if auto-start is configured in userSetup.py."""
        setup_path = _get_user_setup_path()
        if setup_path and os.path.isfile(setup_path):
            try:
                content = open(setup_path).read()
                self._auto_cb.setChecked("maya_connector" in content)
            except Exception:
                self._auto_cb.setChecked(False)

    def _toggle_auto_start(self, state):
        setup_path = _get_user_setup_path()
        if not setup_path:
            cmds.warning("[maya_connector] Could not find Maya scripts folder.")
            return
        _write_auto_start(setup_path, enabled=(state == QtCore.Qt.Checked))

    def closeEvent(self, event):
        self._timer.stop()
        self.deleteLater()
        super().closeEvent(event)


# ── Auto-start helpers ────────────────────────────────────────────────────────

def _get_user_setup_path():
    """Return path to the user's userSetup.py (creates it if missing)."""
    scripts_dir = cmds.internalVar(userScriptDir=True)
    if not scripts_dir:
        return None
    return os.path.join(scripts_dir, "userSetup.py")


_AUTO_START_BLOCK = (
    "\n# ── Maya MCP Connector auto-start ───────────────────────────────────\n"
    "import sys as _sys\n"
    f"_sys.path.insert(0, r'{_TOOL_DIR}')\n"
    "try:\n"
    "    import maya_connector as _mc; _mc.open_port()\n"
    "except Exception as _e:\n"
    "    print('[maya_connector] Auto-start failed:', _e)\n"
    "# ─────────────────────────────────────────────────────────────────────\n"
)


def _write_auto_start(setup_path, enabled):
    marker = "# ── Maya MCP Connector auto-start"
    try:
        existing = open(setup_path).read() if os.path.isfile(setup_path) else ""
    except Exception:
        existing = ""

    # Remove old block
    if marker in existing:
        start = existing.index(marker)
        end_marker = "# ─────────────────────────────────────────────────────────────────────\n"
        end = existing.index(end_marker, start) + len(end_marker)
        existing = existing[:start] + existing[end:]

    if enabled:
        existing = existing.rstrip() + _AUTO_START_BLOCK

    with open(setup_path, "w") as f:
        f.write(existing)

    state = "enabled" if enabled else "disabled"
    cmds.inViewMessage(
        assistMessage=f"<b>MCP auto-start {state}</b> in userSetup.py.",
        position="topCenter", fade=True,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

_tool_window = None


def show():
    """Open the MCP Connector UI."""
    global _tool_window
    try:
        _tool_window.close()
        _tool_window.deleteLater()
    except Exception:
        pass
    _tool_window = MayaConnectorUI()
    _tool_window.show()


# ── Shelf installer ───────────────────────────────────────────────────────────

def _install_shelf_button():
    main_shelf = mel.eval("$gShelfTopLevel = $gShelfTopLevel")

    # Use whichever shelf tab is currently active
    shelf = cmds.tabLayout(main_shelf, query=True, selectTab=True)
    if not shelf:
        shelf = cmds.shelfLayout(SHELF_NAME, parent=main_shelf)

    existing = cmds.shelfLayout(shelf, query=True, childArray=True) or []
    for btn in existing:
        try:
            if cmds.shelfButton(btn, query=True, label=True) == TOOL_LABEL:
                cmds.deleteUI(btn)
        except Exception:
            pass

    icon_path = os.path.join(_TOOL_DIR, TOOL_ICON)
    icon = icon_path if os.path.isfile(icon_path) else "commandButton.png"

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

    # Also open the port immediately on install
    open_port()

    cmds.inViewMessage(
        assistMessage=f"<b>MCP Connector</b> installed on <hl>{shelf}</hl> shelf. Port {MCP_PORT} is open.",
        position="topCenter", fade=True,
    )


def onMayaDroppedPythonFile(*args, **kwargs):
    """Maya calls this when the file is dragged into the viewport."""
    _install_shelf_button()

# ──────────────────────────────────────────────────────────────────────────────
