// content.js - Smart image resolver for Google Images, Pinterest, and Web

function extractGoogleHighRes(element) {
  if (!element) return null;
  // 1. Check enclosing or adjacent anchor with imgurl
  const anchor = element.closest("a[href*='imgurl=']") || 
                (element.parentElement ? element.parentElement.closest("a[href*='imgurl=']") : null);
  if (anchor && anchor.href) {
    try {
      const match = anchor.href.match(/[?&]imgurl=([^&]+)/);
      if (match) {
        return decodeURIComponent(match[1]);
      }
    } catch (e) {}
  }
  return null;
}

function tryCanvasCapture(element) {
  try {
    const img = (element.tagName === "IMG") ? element : (element.querySelector ? element.querySelector("img") : null);
    if (img && img.complete && img.naturalWidth > 16 && img.naturalHeight > 16) {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0);
      return canvas.toDataURL("image/png");
    }
  } catch (e) {}
  return "";
}

function findImageTargets(element) {
  if (!element) return { url: "", fallbackUrl: "" };

  const canvasData = tryCanvasCapture(element);
  const googleHighRes = extractGoogleHighRes(element);
  let thumbUrl = "";

  // 1. Direct IMG element
  if (element.tagName === "IMG") {
    thumbUrl = element.currentSrc || element.src || "";
  }

  // 2. Nearest IMG inside container or parent
  if (!thumbUrl) {
    const nested = element.querySelector("img");
    if (nested) {
      thumbUrl = nested.currentSrc || nested.src || "";
    }
  }

  // 3. Pinterest Pin containers
  if (!thumbUrl) {
    const pin = element.closest("[data-test-id='pin'], [data-test-id='pinWrapper'], div[role='listitem'], .XiG");
    if (pin) {
      const pImg = pin.querySelector("img");
      if (pImg) thumbUrl = pImg.currentSrc || pImg.src || "";
    }
  }

  // 4. Background image CSS
  if (!thumbUrl) {
    let curr = element;
    for (let i = 0; i < 4 && curr; i++) {
      const bg = window.getComputedStyle(curr).backgroundImage;
      if (bg && bg.startsWith("url(")) {
        thumbUrl = bg.slice(4, -1).replace(/["']/g, "");
        break;
      }
      curr = curr.parentElement;
    }
  }

  // Pinterest original high-res upgrade
  let bestUrl = googleHighRes || thumbUrl || canvasData;
  let fallbackUrl = canvasData || thumbUrl || googleHighRes;

  if (bestUrl && bestUrl.includes("pinimg.com")) {
    const upgraded = bestUrl.replace(/\/(?:236x|474x|564x|736x)\//, "/originals/");
    return { url: upgraded, fallbackUrl: fallbackUrl || thumbUrl };
  }

  return { url: bestUrl, fallbackUrl: fallbackUrl };
}

document.addEventListener("contextmenu", (e) => {
  const { url, fallbackUrl } = findImageTargets(e.target);
  if (url || fallbackUrl) {
    chrome.runtime.sendMessage({
      type: "BLENDER_IMAGE_TARGET",
      url: url || fallbackUrl,
      fallbackUrl: fallbackUrl || url
    });
  }
}, true);
