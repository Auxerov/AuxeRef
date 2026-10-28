/**
 * Add to Blender - Background Service Worker / Script
 * Handles context menu creation and sends image URLs to Blender's local bridge server.
 */

const PORTS = [9981, 9982, 9983, 9984];
const api = (typeof browser !== "undefined" && browser.runtime) ? browser : chrome;

async function findBlenderUrl() {
  for (const port of PORTS) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/status`, { cache: "no-store" });
      if (res.ok) {
        return `http://127.0.0.1:${port}`;
      }
    } catch (e) {}
  }
  return null;
}

function setupMenus() {
  api.contextMenus.removeAll(() => {
    // Parent Context Menu
    api.contextMenus.create({
      id: "blender_parent",
      title: "Add to Blender",
      contexts: ["image", "link"]
    });

    // Submenu 1: As Reference Image
    api.contextMenus.create({
      parentId: "blender_parent",
      id: "blender_reference",
      title: "As Reference Image (Empty)",
      contexts: ["image", "link"]
    });

    // Submenu 2: As Image Plane
    api.contextMenus.create({
      parentId: "blender_parent",
      id: "blender_plane",
      title: "As Image Plane (Mesh)",
      contexts: ["image", "link"]
    });

    // Submenu 3: Apply to Active Material
    api.contextMenus.create({
      parentId: "blender_parent",
      id: "blender_material",
      title: "Apply to Active Material",
      contexts: ["image", "link"]
    });
  });
}

api.runtime.onInstalled.addListener(setupMenus);
api.runtime.onStartup.addListener(setupMenus);

function showNotification(title, message) {
  if (api.notifications && api.notifications.create) {
    try {
      api.notifications.create({
        type: "basic",
        iconUrl: "icons/icon48.png",
        title: title,
        message: message
      });
    } catch (e) {
      console.log(`[Notification] ${title}: ${message}`);
    }
  }
}

// Extract real high-resolution target URL from Google Images links/previews
function resolveTargetUrl(info) {
  let targetUrl = info.srcUrl || "";

  // 1. If user right-clicks a Google search result card/link
  if (info.linkUrl) {
    try {
      const u = new URL(info.linkUrl);
      const imgurl = u.searchParams.get("imgurl");
      if (imgurl) {
        return imgurl;
      }
    } catch (e) {}
  }

  // 2. If srcUrl contains embedded imgurl parameter
  if (targetUrl && targetUrl.includes("imgurl=")) {
    try {
      const match = targetUrl.match(/imgurl=([^&]+)/);
      if (match) {
        return decodeURIComponent(match[1]);
      }
    } catch (e) {}
  }

  return targetUrl;
}

api.contextMenus.onClicked.addListener(async (info, tab) => {
  let mode = "REFERENCE";
  if (info.menuItemId === "blender_plane") {
    mode = "PLANE";
  } else if (info.menuItemId === "blender_material") {
    mode = "MATERIAL";
  }

  const targetUrl = resolveTargetUrl(info);
  if (!targetUrl) {
    showNotification("Blender Bridge", "No image URL found.");
    return;
  }

  const rawTitle = (tab && tab.title) ? tab.title.split("-")[0].trim() : "WebImage";

  const blenderUrl = await findBlenderUrl();
  if (!blenderUrl) {
    showNotification(
      "Blender Offline",
      "Could not connect to Blender (tried ports 9981-9984).\nMake sure Blender is running with the add-on enabled!"
    );
    return;
  }

  try {
    const response = await fetch(`${blenderUrl}/add_image`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url: targetUrl,
        mode: mode,
        title: rawTitle
      })
    });

    if (response.ok) {
      const result = await response.json();
      showNotification("Blender Bridge", `Success: Image added to Blender as ${mode}!`);
    } else {
      showNotification("Blender Bridge", `Server error: HTTP ${response.status}`);
    }
  } catch (err) {
    showNotification(
      "Blender Bridge Error",
      "Failed to deliver image to Blender."
    );
  }
});
