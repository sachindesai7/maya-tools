// Figma Asset Exporter Sync plugin
// Reads current selection and sends node IDs to the Python exporter app.

figma.showUI(__html__, { width: 320, height: 260, title: "Asset Exporter Sync" });

function getSelection() {
  const sel = figma.currentPage.selection;
  return sel.map(n => ({
    id:   n.id,
    name: n.name,
    type: n.type,
  }));
}

// Send selection whenever it changes
function pushSelection() {
  figma.ui.postMessage({ type: "selection", nodes: getSelection() });
}

pushSelection();
figma.on("selectionchange", pushSelection);

figma.ui.onmessage = msg => {
  if (msg.type === "close") figma.closePlugin();
};
