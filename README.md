# AuxeRef - Native Reference Image Bridge for Blender

**AuxeRef** is a high-speed, zero-port, zero-server reference image search and browser bridge designed for **Blender 5.0 & 5.2 LTS**. Search Google Images and Pinterest directly inside Blender or right-click any image on the web to open it in your 3D viewport with a single click.

**Author:** Auxerov  
**Version:** 2.4.0  
**Compatibility:** Blender 5.0.0+, Blender 5.2 LTS, Chromium, Thorium, Google Chrome, Brave, Mozilla Firefox

---

## ✨ Key Features

### 1. Instant F8 Search & Quicks Palette
- **Press `F8` anywhere in Blender** to open the search modal. The text input is immediately focused with no extra clicks required.
- **Fast Engine Switching:** Seamlessly toggle between **Google Images** and **Pinterest** using the engine buttons or smart prefix queries (`g <keyword>` or `p <keyword>`).
- **Direct Import on Enter:** Paste any direct image URL (or base64 URI) into the search bar and press Enter to instantly download and import it into your scene.
- **Upright 90° X-Axis Rotation:** All imported references (Empty Reference Image or Mesh Plane) are automatically rotated 90 degrees on the X-axis to face the viewport upright.
- **Interactive Quick References:**
  - View saved references directly under the F8 dialog and the 3D Viewport sidebar (`N > AuxeRef`).
  - Spawn any saved reference into your scene with one click.
  - In-place editing: Rename titles and update web URLs using the inline pencil icon.
  - Re-open original web source pages in your default browser using the link icon.

### 2. Native Browser Extension (`AuxeRef`)
Right-click any image across the web, Google Images, or Pinterest to access the **AuxeRef** menu:
- **`AuxeRef ➔ Open in Blender`**: Instantly downloads and spawns the reference image at your 3D cursor (upright at 90° X).
- **`AuxeRef ➔ Add to Quicks`**: Saves the reference to Blender's persistent Quicks palette without cluttering your active scene.
- **Automatic High-Resolution Resolution:**
  - Automatically fetches the full-resolution `/originals/` image for Pinterest pins.
  - Automatically extracts original high-resolution target URLs from Google Images (`imgurl` parameters).
  - Bypasses hotlink restrictions and CORS blocks using extension background fetch and HTML5 canvas capture.

### 3. Zero-Pink Texture Guarantee (Universal Auto-Healing)
- Built-in automatic format conversion handles modern web formats—including **AVIF**, **WebP**, **GIF**, **HEIC**, **SVG**, **BMP**, and **TIFF**.
- Multi-frame animated GIFs and animated WebPs are automatically flattened into single high-resolution PNG textures.
- Completely prevents Blender pink missing texture errors (`has_data: True` guaranteed).

### 4. Zero-Port Native IPC (No Web Servers)
- Uses standard OS Native Messaging (`stdio` IPC) instead of running a local HTTP web server.
- Completely eliminates socket binding conflicts (`Address already in use`), firewall popups, and security risks.
- Delivers instant sub-millisecond communication between your browser and Blender.

---

## 🚀 Installation

### 1. Install Blender Add-on
1. Download [`blender_web_search.zip`](file:///home/auxerov/blender-image-search/blender_web_search.zip).
2. In Blender, navigate to **Edit > Preferences > Add-ons**.
3. Click the dropdown in the top right, select **Install from Disk...**, choose `blender_web_search.zip`, and enable **AuxeRef**.
4. The add-on will automatically configure the native messaging host and detect your default browser.

### 2. Browser Extension Setup
When enabling the add-on, AuxeRef offers one-click automatic extension installation for your default browser. If you prefer manual installation:

#### Chrome / Thorium / Chromium / Brave
1. Open `chrome://extensions` and enable **Developer mode** in the top right.
2. Click **Load unpacked** and select the [`extension`](file:///home/auxerov/blender-image-search/extension) folder.
   *(Or drag and drop [`extension.crx`](file:///home/auxerov/blender-image-search/extension.crx) into the extensions page).*

#### Mozilla Firefox
1. Open `about:debugging#/runtime/this-firefox`.
2. Click **Load Temporary Add-on...** and select [`extension_firefox/manifest.json`](file:///home/auxerov/blender-image-search/extension_firefox/manifest.json).
   *(Or install the signed package [`add_to_blender_firefox.xpi`](file:///home/auxerov/blender-image-search/add_to_blender_firefox.xpi)).*

---

## 📦 Release Packages

| Package | File | Description |
|---|---|---|
| **Blender Add-on** | [`blender_web_search.zip`](blender_web_search.zip) | Complete add-on package for Blender 5.0 & 5.2 LTS |
| **Chrome / Chromium** | [`extension.crx`](extension.crx) | Pre-packed Chromium extension |
| **Chrome Source ZIP** | [`add_to_blender_chrome.zip`](add_to_blender_chrome.zip) | Unpacked Chrome extension source archive |
| **Firefox Add-on** | [`add_to_blender_firefox.xpi`](add_to_blender_firefox.xpi) | Pre-packed Firefox extension package |
| **Firefox Source ZIP** | [`add_to_blender_firefox.zip`](add_to_blender_firefox.zip) | Unpacked Firefox extension source archive |

---

## ⌨️ Shortcuts & Navigation

| Shortcut | Context | Action |
|---|---|---|
| **`F8`** | 3D View / Anywhere | Open AuxeRef Search modal with autofocus |
| **`Tab`** | Search Modal | Cycle between Search Input, Engine buttons, and Quicks list |
| **`Enter`** | Search Modal | Execute web search or immediately import pasted URL |
| **`N > AuxeRef`** | 3D View Sidebar | Open persistent Quicks shelf and import options |

---

## 🛡️ License & Credits
- **Author:** Auxerov
- **License:** MIT License
