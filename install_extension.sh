#!/usr/bin/env bash
# Helper script to load or install the "Add to Blender" extension in browsers.

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHROME_EXT_DIR="$DIR/extension"
FIREFOX_EXT_FILE="$DIR/extension_firefox/manifest.json"

echo "============================================================"
echo "Add to Blender Browser Extension Setup"
echo "============================================================"
echo ""
echo "1) CHROME / THORIUM / CHROMIUM / BRAVE:"
echo "   a. Open your browser and go to: chrome://extensions"
echo "   b. Turn ON 'Developer mode' (Geliştirici modu) in top-right."
echo "   c. Click 'Load unpacked' (Paketlenmemiş öğe yükle)."
echo "   d. Select this directory:"
echo "      $CHROME_EXT_DIR"
echo ""
echo "2) FIREFOX:"
echo "   a. Open Firefox and go to: about:debugging#/runtime/this-firefox"
echo "   b. Click 'Load Temporary Add-on...' (Geçici Eklenti Yükle...)"
echo "   c. Select this manifest file:"
echo "      $FIREFOX_EXT_FILE"
echo ""
echo "============================================================"
echo "Available ZIP Packages:"
echo "  - Chrome/Thorium: $DIR/add_to_blender_chrome.zip"
echo "  - Firefox:        $DIR/add_to_blender_firefox.zip"
echo "  - Blender Add-on: $DIR/blender_web_search.zip"
echo "============================================================"
