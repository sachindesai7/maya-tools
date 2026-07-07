// Service worker: fetches files from Google Drive on behalf of the popup.
// Runs here (extension origin) so host_permissions apply and CORS is not an issue.

function extractDriveFileId(url) {
  const m =
    url.match(/\/file\/d\/([\w-]+)/) ||
    url.match(/[?&]id=([\w-]+)/) ||
    url.match(/\/d\/([\w-]+)/);
  return m ? m[1] : null;
}

function bufferToBase64(buf) {
  const bytes = new Uint8Array(buf);
  let binary = "";
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  }
  return btoa(binary);
}

function fileNameFromDisposition(header) {
  if (!header) return null;
  const utf8 = header.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8) return decodeURIComponent(utf8[1]);
  const plain = header.match(/filename="?([^";]+)"?/i);
  return plain ? plain[1] : null;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== "FETCH_DRIVE_FILE") return;

  (async () => {
    try {
      const fileId = extractDriveFileId(msg.url);
      if (!fileId) throw new Error("Could not find a file ID in that link. Use a link like https://drive.google.com/file/d/FILE_ID/view");

      const res = await fetch(`https://drive.google.com/uc?export=download&id=${fileId}`);
      if (!res.ok) throw new Error(`Drive returned HTTP ${res.status}`);

      const contentType = (res.headers.get("content-type") || "").split(";")[0];
      if (contentType.includes("text/html")) {
        throw new Error("Drive returned a web page instead of the file. Check the file is shared as 'Anyone with the link' and the link points to a file, not a folder.");
      }

      const buf = await res.arrayBuffer();
      const fileName = fileNameFromDisposition(res.headers.get("content-disposition"));

      sendResponse({
        ok: true,
        base64: bufferToBase64(buf),
        mimeType: contentType || "application/octet-stream",
        fileName: fileName,
        size: buf.byteLength
      });
    } catch (e) {
      sendResponse({ ok: false, error: e.message });
    }
  })();

  return true; // keep the message channel open for the async response
});
