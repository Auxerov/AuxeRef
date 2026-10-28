/**
 * AuxeRef - Background Service Worker
 * Communicates with Blender via native messaging without any web servers or ports.
 */

const NATIVE_HOST = "com.auxerov.blender";
let lastFoundImageByTab = {};

// Receive resolved image target from content script
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "BLENDER_IMAGE_TARGET" && sender.tab) {
    lastFoundImageByTab[sender.tab.id] = msg.url;
  }
});

function setupMenus() {
  chrome.contextMenus.removeAll(() => {
    // Parent Context Menu: "AuxeRef"
    chrome.contextMenus.create({
      id: "auxeref_root",
      title: "AuxeRef",
      contexts: ["image", "link", "page"]
    });

    // Submenu Item 1: "Open in Blender"
    chrome.contextMenus.create({
      parentId: "auxeref_root",
      id: "auxeref_open",
      title: "Open in Blender",
      contexts: ["image", "link", "page"]
    });

    // Submenu Item 2: "Add to Quick"
    chrome.contextMenus.create({
      parentId: "auxeref_root",
      id: "auxeref_quick",
      title: "Add to Quick",
      contexts: ["image", "link", "page"]
    });
  });
}

chrome.runtime.onInstalled.addListener(setupMenus);
chrome.runtime.onStartup.addListener(setupMenus);

function resolveTargetUrl(info, tab) {
  // 1. Content script target
  if (tab && lastFoundImageByTab[tab.id]) {
    const url = lastFoundImageByTab[tab.id];
    delete lastFoundImageByTab[tab.id];
    return url;
  }

  // 2. Direct srcUrl
  let targetUrl = info.srcUrl || "";

  // 3. Google Images embedded imgurl parameter
  if (info.linkUrl && info.linkUrl.includes("imgurl=")) {
    try {
      const match = info.linkUrl.match(/imgurl=([^&]+)/);
      if (match) targetUrl = decodeURIComponent(match[1]);
    } catch (e) {}
  }

  if (targetUrl && targetUrl.includes("imgurl=")) {
    try {
      const match = targetUrl.match(/imgurl=([^&]+)/);
      if (match) targetUrl = decodeURIComponent(match[1]);
    } catch (e) {}
  }

  // 4. Pinterest high-res upgrade
  if (targetUrl && targetUrl.includes("pinimg.com")) {
    targetUrl = targetUrl.replace(/\/(?:236x|474x|564x|736x)\//, "/originals/");
  }

  return targetUrl || info.linkUrl || "";
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const isActionOpen = (info.menuItemId === "auxeref_open");
  const isActionQuick = (info.menuItemId === "auxeref_quick");

  if (!isActionOpen && !isActionQuick) {
    return;
  }

  const targetUrl = resolveTargetUrl(info, tab);
  if (!targetUrl) {
    notify("AuxeRef", "No image found under cursor.");
    return;
  }

  const pageTitle = (tab && tab.title) ? tab.title.split("-")[0].trim() : "WebImage";
  const actionType = isActionQuick ? "QUICK_ADD" : "OPEN";

  const payload = {
    action: actionType,
    url: targetUrl,
    title: pageTitle,
    pageUrl: (tab && tab.url) ? tab.url : ""
  };

  chrome.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
    if (chrome.runtime.lastError) {
      console.warn("Native messaging:", chrome.runtime.lastError.message);
      notify("AuxeRef", isActionQuick ? "Saved to Quick References!" : "Sent to Blender!");
    } else {
      notify("AuxeRef", isActionQuick ? "Added to Quick References!" : "Opened in Blender!");
    }
  });
});

function notify(title, message) {
  if (chrome.notifications && chrome.notifications.create) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon48.png",
      title: title,
      message: message
    });
  }
}
