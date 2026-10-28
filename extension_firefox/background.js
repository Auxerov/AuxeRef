/**
 * Open in Blender - Background Service Worker
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

// Single clean menu choice: "Open in Blender"
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "open_in_blender",
      title: "Open in Blender",
      contexts: ["image", "link", "page"]
    });
  });
});

function resolveTargetUrl(info, tab) {
  // 1. Content script found target (especially for Pinterest overlay divs)
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
  if (info.menuItemId === "open_in_blender") {
    const targetUrl = resolveTargetUrl(info, tab);
    if (!targetUrl) {
      notify("Open in Blender", "No image found under cursor.");
      return;
    }

    const pageTitle = (tab && tab.title) ? tab.title.split("-")[0].trim() : "WebImage";

    const payload = {
      url: targetUrl,
      title: pageTitle,
      pageUrl: (tab && tab.url) ? tab.url : ""
    };

    // Send directly via Native Messaging
    chrome.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("Native messaging:", chrome.runtime.lastError.message);
        notify("Open in Blender", "Sent to Blender inbox!");
      } else {
        notify("Open in Blender", "Image opened in Blender!");
      }
    });
  }
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
