const NATIVE_HOST = "com.auxerov.blender";
let lastTargetsByTab = {};

const browserApi = (typeof browser !== "undefined" && browser.runtime) ? browser : chrome;

browserApi.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "BLENDER_IMAGE_TARGET" && sender.tab) {
    lastTargetsByTab[sender.tab.id] = {
      url: msg.url,
      fallbackUrl: msg.fallbackUrl || msg.url
    };
  }
});

const MENU_ITEMS = [
  {
    id: "auxeref_open",
    title: "Open in Blender",
    contexts: ["all"]
  },
  {
    id: "auxeref_quick",
    title: "Add to Quicks",
    contexts: ["all"]
  }
];

let initRunning = false;

function createMenuAsync(item) {
  return new Promise((resolve) => {
    browserApi.contextMenus.create(item, () => {
      resolve();
    });
  });
}

async function setupMenus() {
  if (initRunning) return;
  initRunning = true;
  try {
    await new Promise((resolve) => {
      browserApi.contextMenus.removeAll(() => {
        resolve();
      });
    });

    for (const item of MENU_ITEMS) {
      await createMenuAsync(item);
    }
  } catch (err) {
    console.warn("AuxeRef setupMenus error:", err);
  } finally {
    initRunning = false;
  }
}

browserApi.runtime.onInstalled.addListener(() => { setupMenus(); });
browserApi.runtime.onStartup.addListener(() => { setupMenus(); });
setupMenus();

function resolveTarget(info, tab) {
  let url = "";
  let fallbackUrl = "";

  if (tab && lastTargetsByTab[tab.id]) {
    url = lastTargetsByTab[tab.id].url;
    fallbackUrl = lastTargetsByTab[tab.id].fallbackUrl;
    delete lastTargetsByTab[tab.id];
  }

  if (!url && info.srcUrl) {
    url = info.srcUrl;
    fallbackUrl = info.srcUrl;
  }

  if (info.linkUrl && info.linkUrl.includes("imgurl=")) {
    try {
      const match = info.linkUrl.match(/[?&]imgurl=([^&]+)/);
      if (match) {
        url = decodeURIComponent(match[1]);
      }
    } catch (e) {}
  }

  if (url && url.includes("pinimg.com")) {
    url = url.replace(/\/(?:236x|474x|564x|736x)\//, "/originals/");
  }

  return {
    url: url || info.linkUrl || "",
    fallbackUrl: fallbackUrl || url || ""
  };
}

async function blobToDataUrl(blob) {
  const buffer = await blob.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  const mimeType = blob.type || "image/png";
  return `data:${mimeType};base64,${base64}`;
}

async function fetchImageAsDataUrl(url) {
  if (!url) return null;
  if (url.startsWith("data:image/")) return url;

  try {
    const res = await fetch(url);
    if (res.ok) {
      const blob = await res.blob();
      if (blob.size > 50) {
        return await blobToDataUrl(blob);
      }
    }
  } catch (err) {}

  try {
    const res = await fetch(url, { credentials: "include" });
    if (res.ok) {
      const blob = await res.blob();
      if (blob.size > 50) {
        return await blobToDataUrl(blob);
      }
    }
  } catch (err) {}

  return null;
}

browserApi.contextMenus.onClicked.addListener(async (info, tab) => {
  const isActionOpen = (info.menuItemId === "auxeref_open");
  const isActionQuick = (info.menuItemId === "auxeref_quick");

  if (!isActionOpen && !isActionQuick) {
    return;
  }

  const { url: targetUrl, fallbackUrl } = resolveTarget(info, tab);
  if (!targetUrl) {
    notify("AuxeRef", "No image found under cursor.");
    return;
  }

  const pageTitle = (tab && tab.title) ? tab.title.split("-")[0].trim() : "WebImage";
  const actionType = isActionQuick ? "QUICK_ADD" : "OPEN";

  let finalUrl = targetUrl;
  let fetched = await fetchImageAsDataUrl(targetUrl);
  if (!fetched && fallbackUrl && fallbackUrl !== targetUrl) {
    fetched = await fetchImageAsDataUrl(fallbackUrl);
  }
  // Native Messaging max length is 1024*1024 bytes.
  // Only use base64 dataUrl if under 800KB. For larger images, Blender downloads directly.
  if (fetched && fetched.length < 800000) {
    finalUrl = fetched;
  }

  const payload = {
    action: actionType,
    url: finalUrl,
    fallback_url: fallbackUrl || "",
    original_url: targetUrl,
    title: pageTitle,
    pageUrl: (tab && tab.url) ? tab.url : ""
  };

  browserApi.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
    const err = browserApi.runtime.lastError;
    if (err) {
      console.warn("Native messaging error:", err.message);
    }
    notify("AuxeRef", isActionQuick ? "Added to Quicks!" : "Sent to Blender!");
  });
});

function notify(title, message) {
  if (browserApi.notifications && browserApi.notifications.create) {
    browserApi.notifications.create({
      type: "basic",
      iconUrl: "icons/icon48.png",
      title: title,
      message: message
    });
  }
}
