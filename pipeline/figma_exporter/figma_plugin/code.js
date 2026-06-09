// Figma Asset Exporter — Plugin backend
// Exports image/video assets directly to a local folder — no API token needed.

figma.showUI(__html__, { width: 340, height: 400, title: "Asset Exporter" });

// ── Tree walker ───────────────────────────────────────────────────────────────
const CONTAINERS = new Set(['SECTION','FRAME','GROUP','COMPONENT','INSTANCE','BOOLEAN_OPERATION']);

function collectAssets(roots) {
  const results = [];

  function walk(node, pathParts) {
    // ── Approach 0a: MEDIA node (FigJam embedded video) ──────────────────────
    // Figma plugin API cannot retrieve video bytes from FigJam MEDIA nodes.
    // Mark as un-exportable so the UI shows a manual-download message.
    if (node.type === 'MEDIA') {
      results.push({
        node,
        pathParts:    [...pathParts],
        fillType:     'VIDEO',
        hash:         null,           // force skip path
        useVideoApi:  false,
        mediaSkip:    true,           // flag: show helpful message, not generic error
      });
      return;
    }

    // ── Approach 0b: dedicated VIDEO node type ────────────────────────────────
    if (node.type === 'VIDEO') {
      results.push({
        node,
        pathParts:   [...pathParts],
        fillType:    'VIDEO',
        hash:        node.videoHash || null,
        useVideoApi: typeof figma.getVideoByHash === 'function',
      });
      return;
    }

    // ── Approach 1: node-level videoHash (some Figma versions store it here) ──
    if (node.videoHash !== undefined && node.videoHash !== null) {
      console.log('[AssetExporter] node-level videoHash on "' + node.name + '" type=' + node.type, 'hash=' + node.videoHash);
      results.push({
        node,
        pathParts:   [...pathParts],
        fillType:    'VIDEO',
        hash:        node.videoHash,
        useVideoApi: true,
      });
      // still fall through to check fills too (might have IMAGE fills as well)
    }

    // ── Approach 2: fills array ────────────────────────────────────────────────
    if ('fills' in node && Array.isArray(node.fills)) {
      for (const fill of node.fills) {
        if (fill.type === 'IMAGE' && fill.imageHash) {
          // Only add if we didn't already add this node via node-level videoHash
          if (!node.videoHash) {
            results.push({
              node,
              pathParts: [...pathParts],
              fillType:  'IMAGE',
              hash:      fill.imageHash,
            });
          }
          break;
        }
        if (fill.type === 'VIDEO') {
          const videoHash = fill.videoHash;
          const imageHash = fill.imageHash;
          console.log(
            '[AssetExporter] VIDEO fill on "' + node.name + '" (type=' + node.type + ')',
            'fill.videoHash=' + videoHash,
            'fill.imageHash=' + imageHash,
            'figma.getVideoByHash=' + typeof figma.getVideoByHash
          );
          // Push even if both are null — shows as skip with reason in UI
          if (!node.videoHash) {  // avoid duplicate if already added via node-level
            results.push({
              node,
              pathParts:   [...pathParts],
              fillType:    'VIDEO',
              hash:        videoHash || imageHash || null,
              useVideoApi: !!videoHash,
            });
          }
          break;
        }
      }
    }
    if ('children' in node) {
      for (const child of node.children) {
        const childPath = CONTAINERS.has(child.type)
          ? [...pathParts, child.name]
          : pathParts;
        walk(child, childPath);
      }
    }
  }

  for (const root of roots) {
    walk(root, [root.name]);
  }
  return results;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

// Wraps a promise with a timeout — rejects after `ms` milliseconds
function withTimeout(promise, ms) {
  return new Promise(function(resolve, reject) {
    const timer = setTimeout(function() {
      reject(new Error('Timed out after ' + ms + 'ms'));
    }, ms);
    promise.then(
      function(v) { clearTimeout(timer); resolve(v); },
      function(e) { clearTimeout(timer); reject(e); }
    );
  });
}

// ── Selection sync ────────────────────────────────────────────────────────────
function pushSelection() {
  const sel = figma.currentPage.selection;
  figma.ui.postMessage({
    type:  'selection',
    nodes: sel.map(function(n) { return { id: n.id, name: n.name, type: n.type }; }),
    count: sel.length,
  });
}

pushSelection();
figma.on('selectionchange', pushSelection);

// ── Message handler ───────────────────────────────────────────────────────────
figma.ui.onmessage = async function(msg) {

  if (msg.type === 'close') { figma.closePlugin(); return; }

  // ── Preview (count assets without fetching bytes) ──────────────────────────
  if (msg.type === 'preview') {
    const sel    = figma.currentPage.selection;
    const roots  = (msg.useSelection && sel.length > 0) ? sel : [figma.currentPage];
    const assets = collectAssets(roots);

    // Debug scan — collect ALL node types + any video-related nodes
    const videoDebug = [];
    const allTypes = {};   // type → count
    function scanForVideos(node) {
      // Count every node type we see
      allTypes[node.type] = (allTypes[node.type] || 0) + 1;

      // 0. MEDIA node (FigJam)
      if (node.type === 'MEDIA') {
        videoDebug.push('MEDIA "' + node.name + '" mediaData.hash=' + (node.mediaData && node.mediaData.hash));
      }
      // 1. dedicated VIDEO node type
      if (node.type === 'VIDEO') {
        videoDebug.push('node.type=VIDEO "' + node.name + '" videoHash=' + node.videoHash + ' getVideoByHash=' + typeof figma.getVideoByHash);
      }
      // 2. any node that HAS a videoHash property (even if null)
      if ('videoHash' in node) {
        videoDebug.push('videoHash prop on [' + node.type + '] "' + node.name + '"=' + node.videoHash);
      }
      // 3. VIDEO fills
      if ('fills' in node && Array.isArray(node.fills)) {
        for (const fill of node.fills) {
          if (fill.type === 'VIDEO') {
            videoDebug.push('fill.VIDEO on [' + node.type + '] "' + node.name + '" videoHash=' + fill.videoHash + ' imageHash=' + fill.imageHash);
          }
        }
      }
      // 4. any node whose name includes "video" (case-insensitive)
      if (node.name && node.name.toLowerCase().includes('video')) {
        videoDebug.push('name~video: [' + node.type + '] "' + node.name + '"');
      }
      if ('children' in node) { node.children.forEach(scanForVideos); }
    }
    roots.forEach(scanForVideos);
    // Always show all types found (so we know the full tree structure)
    videoDebug.unshift('ALL TYPES: ' + Object.keys(allTypes).map(function(k){ return k+'×'+allTypes[k]; }).join('  '));

    figma.ui.postMessage({
      type:       'preview-result',
      count:      assets.length,
      paths:      assets.slice(0, 8).map(function(a) {
        return a.pathParts.join('/') + '/' + a.node.name;
      }),
      videoDebug: videoDebug,
    });
    return;
  }

  // ── Export ─────────────────────────────────────────────────────────────────
  if (msg.type === 'start-export') {
    const sel    = figma.currentPage.selection;
    const roots  = (msg.useSelection && sel.length > 0) ? sel : [figma.currentPage];
    const assets = collectAssets(roots);

    if (assets.length === 0) {
      figma.ui.postMessage({ type: 'export-done', total: 0, skipped: 0 });
      return;
    }

    figma.ui.postMessage({ type: 'export-start', total: assets.length });

    let skipped = 0;

    for (let i = 0; i < assets.length; i++) {
      const { node, pathParts, fillType, hash, useVideoApi, mediaSkip } = assets[i];

      // Notify UI we're starting this asset
      figma.ui.postMessage({
        type:  'export-fetching',
        name:  node.name,
        index: i,
        total: assets.length,
      });

      // FigJam MEDIA video — create placeholder .txt so folder is created,
      // then continue to next asset (don't count as skipped)
      if (mediaSkip) {
        const note = [
          'This video could not be exported automatically.',
          '',
          'To export the original video:',
          '  1. Open Figma',
          '  2. Right-click the video node "' + node.name + '"',
          '  3. Click "Download"',
        ].join('\n');
        const noteBytes = new Uint8Array(note.length);
        for (let j = 0; j < note.length; j++) { noteBytes[j] = note.charCodeAt(j); }
        figma.ui.postMessage({
          type:          'export-asset',
          name:          '_download_video_here',
          pathParts:     pathParts,
          assetType:     'placeholder',
          bytes:         noteBytes.buffer,
          index:         i,
          total:         assets.length,
          isPlaceholder: true,
        });
        continue;
      }

      // Generic no-hash skip
      if (!hash) {
        skipped++;
        figma.ui.postMessage({
          type:  'export-skip',
          name:  node.name,
          reason:'No accessible hash',
          index: i,
          total: assets.length,
        });
        continue;
      }

      try {
        let mediaObj;

        if (fillType === 'VIDEO' && useVideoApi && typeof figma.getVideoByHash === 'function') {
          // Use dedicated video API when available (returns actual video bytes)
          mediaObj = figma.getVideoByHash(hash);
        } else {
          mediaObj = figma.getImageByHash(hash);
        }

        if (!mediaObj) {
          throw new Error('getImageByHash/getVideoByHash returned null');
        }

        // 120-second timeout — videos and large images need more time
        const bytes = await withTimeout(mediaObj.getBytesAsync(), 120000);

        // Send ArrayBuffer directly — much faster than Array.from() for large files
        figma.ui.postMessage({
          type:      'export-asset',
          name:      node.name,
          pathParts: pathParts,
          assetType: fillType === 'VIDEO' ? 'video' : 'image',
          bytes:     bytes.buffer,   // ArrayBuffer — structured-cloned, no copy overhead
          index:     i,
          total:     assets.length,
        });

      } catch(e) {
        skipped++;
        figma.ui.postMessage({
          type:    'export-skip',
          name:    node.name,
          reason:  e.message,
          index:   i,
          total:   assets.length,
        });
      }
    }

    figma.ui.postMessage({ type: 'export-done', total: assets.length, skipped });
  }
};
