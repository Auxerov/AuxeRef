"""Local HTTP bridge server connecting WebExtensions (Chrome/Firefox) to Blender."""
import os
import json
import threading
import queue
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import bpy
from . import importer

DEFAULT_PORT = 9981

server_instance = None
server_thread = None
import_queue = queue.Queue()

def render_setup_html(browser_type: str = "chrome", browser_name: str = "Thorium Browser") -> bytes:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    chrome_ext_dir = os.path.join(base_dir, "extension_chrome")
    firefox_ext_dir = os.path.join(base_dir, "extension_firefox")
    firefox_manifest = os.path.join(firefox_ext_dir, "manifest.json")

    is_chrome = (browser_type.lower() != "firefox")

    if is_chrome:
        instructions = f"""
        <div class="step">
          <b>Step 1:</b> The extension folder path was copied to your clipboard:
          <div class="path-box">
            <span id="ext-path">{chrome_ext_dir}</span>
            <button class="btn-secondary" onclick="copyPath()">📋 Copy</button>
          </div>
        </div>
        <div class="step">
          <b>Step 2:</b> Open your browser extensions manager:
          <div style="margin-top: 8px;">
            <a href="chrome://extensions" target="_blank" style="color:#38bdf8; text-decoration:none; font-weight:bold;">👉 Click here or type chrome://extensions in a new tab</a>
          </div>
        </div>
        <div class="step">
          <b>Step 3:</b> Turn <b>ON</b> "Developer mode" (top-right), click <b>"Load unpacked"</b>, and select the folder path above (or paste with Ctrl+V).
        </div>
        <div class="step" style="border-left-color: #2ecc71;">
          <b>⚡ Auto-Configured:</b> The extension package has also been registered in your <code>~/.config/</code> external extensions directory!
        </div>
        """
    else:
        instructions = f"""
        <div class="step">
          <b>Option A (Direct 1-Click Install):</b>
          <div style="margin-top: 10px;">
            <a href="/download/firefox.xpi" download="add_to_blender.xpi" style="display:inline-block; text-decoration:none;">
              <button>📦 Install Add-on to Firefox (.xpi)</button>
            </a>
          </div>
        </div>
        <div class="step">
          <b>Option B (Temporary Add-on for Debugging):</b>
          <p>1. Open <code>about:debugging#/runtime/this-firefox</code> in a new tab.</p>
          <p>2. Click <b>"Load Temporary Add-on..."</b> and choose this manifest file:</p>
          <div class="path-box">
            <span id="ext-path">{firefox_manifest}</span>
            <button class="btn-secondary" onclick="copyPath()">📋 Copy</button>
          </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Blender Image Bridge Setup</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #181818;
      color: #eaeaea;
      margin: 0;
      padding: 40px 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .card {{
      background: #242424;
      border: 1px solid #383838;
      border-radius: 12px;
      max-width: 620px;
      width: 100%;
      padding: 30px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }}
    h1 {{
      font-size: 22px;
      margin-top: 0;
      color: #eb7814;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .badge {{
      display: inline-block;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      background: #1b4d2e;
      color: #4ade80;
      margin-bottom: 20px;
    }}
    .step {{
      background: #1e1e1e;
      border-radius: 8px;
      padding: 14px 18px;
      margin: 12px 0;
      border-left: 4px solid #eb7814;
      font-size: 14px;
      line-height: 1.5;
    }}
    .path-box {{
      background: #111;
      border: 1px solid #444;
      border-radius: 6px;
      padding: 8px 12px;
      font-family: monospace;
      font-size: 12px;
      color: #38bdf8;
      word-break: break-all;
      margin: 8px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}
    button {{
      background: #eb7814;
      color: white;
      border: none;
      border-radius: 6px;
      padding: 10px 18px;
      font-weight: 600;
      cursor: pointer;
      font-size: 13px;
    }}
    button:hover {{ background: #f98e32; }}
    .btn-secondary {{
      background: #374151;
      color: #e5e7eb;
      padding: 6px 12px;
      font-size: 12px;
    }}
    .btn-secondary:hover {{ background: #4b5563; }}
    .footer {{
      margin-top: 24px;
      font-size: 13px;
      color: #888;
      text-align: center;
    }}
    .test-box {{
      margin-top: 24px;
      padding-top: 18px;
      border-top: 1px solid #383838;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>
      <span>🎨</span> Blender Image Bridge Setup
    </h1>
    <div class="badge">🟢 Blender Bridge is Online (Port {DEFAULT_PORT})</div>
    <p style="color:#aaa; font-size:14px; margin-top:0;">
      Target Browser: <b>{browser_name}</b> ({'Chromium-based' if is_chrome else 'Firefox'})
    </p>

    {instructions}

    <div class="test-box">
      <div>
        <b>Ready to test?</b>
        <div style="font-size:12px; color:#888;">Open Google Images and try Right Click ➔ Add to Blender</div>
      </div>
      <a href="https://www.google.com/search?q=concept+art+3d&udm=2" target="_blank" style="text-decoration:none;">
        <button>Search Google Images</button>
      </a>
    </div>
  </div>

  <div class="footer">
    Blender 5.0 Image Bridge • Running on 127.0.0.1:{DEFAULT_PORT}
  </div>

  <script>
    function copyPath() {{
      const text = document.getElementById("ext-path").innerText;
      navigator.clipboard.writeText(text).then(() => {{
        alert("Copied to clipboard: " + text);
      }});
    }}
  </script>
</body>
</html>
"""
    return html.encode("utf-8")


class BlenderBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy standard HTTP access logging to Blender console
        return

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            data = {
                "status": "online",
                "blender_version": bpy.app.version_string,
                "port": DEFAULT_PORT,
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif path in ("/setup", "/install"):
            params = urllib.parse.parse_qs(parsed.query)
            b_type = params.get("browser", ["chrome"])[0]
            b_name = params.get("name", ["Thorium Browser"])[0]
            
            html_bytes = render_setup_html(b_type, b_name)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(html_bytes)

        elif path == "/download/firefox.xpi":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            xpi_path = os.path.join(base_dir, "add_to_blender_firefox.xpi")
            if not os.path.exists(xpi_path):
                xpi_path = os.path.join(os.path.dirname(base_dir), "add_to_blender_firefox.xpi")

            if os.path.exists(xpi_path):
                with open(xpi_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/x-xpinstall")
                self.send_header("Content-Disposition", 'inline; filename="add_to_blender.xpi"')
                self.send_header("Content-Length", str(len(content)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()

        elif path == "/download/extension.crx":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            crx_path = os.path.join(base_dir, "extension.crx")
            if not os.path.exists(crx_path):
                crx_path = os.path.join(os.path.dirname(base_dir), "extension.crx")

            if os.path.exists(crx_path):
                with open(crx_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/x-chrome-extension")
                self.send_header("Content-Disposition", 'inline; filename="add_to_blender.crx"')
                self.send_header("Content-Length", str(len(content)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/add_image":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "Empty request body"}')
                return

            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(f'{{"status": "error", "message": "Invalid JSON: {e}"}}'.encode("utf-8"))
                return

            url = payload.get("url", "").strip()
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "Missing image url"}')
                return

            # Push to queue
            import_queue.put(payload)

            # Register timer on Blender's main event loop
            bpy.app.timers.register(_process_queue, first_interval=0.01)

            # Immediate response to browser
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Image sent to Blender"}')
        else:
            self.send_response(404)
            self.end_headers()

def _process_queue():
    """Executed strictly on Blender's main thread via bpy.app.timers."""
    while not import_queue.empty():
        try:
            payload = import_queue.get_nowait()
        except queue.Empty:
            break

        url = payload.get("url", "")
        title = payload.get("title", "BrowserImage")
        
        mode = payload.get("mode")
        if not mode or mode == "AUTO":
            mode = getattr(bpy.context.scene, "web_search_default_mode", "REFERENCE")

        try:
            filepath = importer.download_or_decode_image(url, title)
            obj, desc = importer.import_image_into_scene(filepath, mode=mode, title=title)
            print(f"[Blender Web Bridge] Successfully added '{obj.name}' as {desc} into scene.")
            
            def _report():
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == "VIEW_3D":
                            area.tag_redraw()
            _report()

        except Exception as e:
            print(f"[Blender Web Bridge Error] Failed to import image: {e}")

    return None

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def get_active_port() -> int:
    global DEFAULT_PORT
    return DEFAULT_PORT

def start_server(port=DEFAULT_PORT):
    global server_instance, server_thread, DEFAULT_PORT

    if server_instance is not None:
        return True

    # Try requested port, then subsequent ports if occupied
    for candidate_port in range(port, port + 5):
        try:
            server_instance = ReusableHTTPServer(("127.0.0.1", candidate_port), BlenderBridgeHandler)
            DEFAULT_PORT = candidate_port
            server_thread = threading.Thread(target=server_instance.serve_forever, daemon=True)
            server_thread.start()
            print(f"[Blender Web Bridge] HTTP server listening on http://127.0.0.1:{candidate_port}")
            return True
        except OSError as e:
            if e.errno == 98:  # Address already in use
                continue
            else:
                print(f"[Blender Web Bridge Error] Could not start HTTP server: {e}")
                break

    print(f"[Blender Web Bridge Error] All ports in range {port}..{port+4} are in use.")
    server_instance = None
    server_thread = None
    return False

def stop_server():
    global server_instance, server_thread
    if server_instance is not None:
        try:
            server_instance.shutdown()
            server_instance.server_close()
        except Exception:
            pass
        server_instance = None
        server_thread = None
        print("[Blender Web Bridge] HTTP server stopped.")
