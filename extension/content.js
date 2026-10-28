// content.js - Smart image finder for Pinterest, Google Images, and general web pages

function cleanImageUrl(url) {
  if (!url) return null;
  
  // Clean query strings or styles appended to image extensions
  url = url.split("?")[0];
  
  // Pinterest high-res upgrade: replace 236x/474x/564x/736x with originals
  if (url.includes("pinimg.com")) {
    url = url.replace(/\/(?:236x|474x|564x|736x)\//, "/originals/");
  }
  
  return url;
}

function findBestImage(element) {
  if (!element) return null;

  // 1. Direct IMG element
  if (element.tagName === "IMG" && element.src) {
    return cleanImageUrl(element.src);
  }

  // 2. Pinterest Pin containers
  const pinContainer = element.closest("[data-test-id='pin'], [data-test-id='pinWrapper'], div[role='listitem'], .XiG");
  if (pinContainer) {
    const img = pinContainer.querySelector("img");
    if (img && img.src) {
      return cleanImageUrl(img.src);
    }
  }

  // 3. Any nested img tag
  const nestedImg = element.querySelector("img");
  if (nestedImg && nestedImg.src) {
    return cleanImageUrl(nestedImg.src);
  }

  // 4. Background image CSS
  const bg = window.getComputedStyle(element).backgroundImage;
  if (bg && bg.startsWith("url(")) {
    const raw = bg.slice(4, -1).replace(/["']/g, "");
    return cleanImageUrl(raw);
  }

  // 5. Parent with background image
  let parent = element.parentElement;
  for (let i = 0; i < 3 && parent; i++) {
    const pBg = window.getComputedStyle(parent).backgroundImage;
    if (pBg && pBg.startsWith("url(")) {
      const raw = pBg.slice(4, -1).replace(/["']/g, "");
      return cleanImageUrl(raw);
    }
    parent = parent.parentElement;
  }

  return null;
}

document.addEventListener("contextmenu", (e) => {
  const imgUrl = findBestImage(e.target);
  if (imgUrl) {
    chrome.runtime.sendMessage({
      type: "BLENDER_IMAGE_TARGET",
      url: imgUrl
    });
  }
}, true);
