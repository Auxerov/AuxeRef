"""Local HTTP bridge server connecting WebExtensions (Chrome/Firefox) to Blender."""
import json
import threading
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler
import bpy
from . import importer

DEFAULT_PORT = 9981

server_instance = None
server_thread = None
import_queue = queue.Queue()

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
        if self.path in ("/", "/status"):
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
        
        # Get import mode (from request, or fallback to scene setting)
        mode = payload.get("mode")
        if not mode or mode == "AUTO":
            mode = getattr(bpy.context.scene, "web_search_default_mode", "REFERENCE")

        try:
            filepath = importer.download_or_decode_image(url, title)
            obj, desc = importer.import_image_into_scene(filepath, mode=mode, title=title)
            print(f"[Blender Web Bridge] Successfully added '{obj.name}' as {desc} into scene.")
            
            # Show top-bar info message in active window
            def _report():
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == "VIEW_3D":
                            area.tag_redraw()
            _report()

        except Exception as e:
            print(f"[Blender Web Bridge Error] Failed to import image: {e}")

    return None  # Do not re-run timer

def start_server(port=DEFAULT_PORT):
    global server_instance, server_thread, DEFAULT_PORT
    DEFAULT_PORT = port

    if server_instance is not None:
        return True

    try:
        server_instance = HTTPServer(("127.0.0.1", port), BlenderBridgeHandler)
        server_thread = threading.Thread(target=server_instance.serve_forever, daemon=True)
        server_thread.start()
        print(f"[Blender Web Bridge] HTTP server listening on http://127.0.0.1:{port}")
        return True
    except Exception as e:
        print(f"[Blender Web Bridge Error] Could not start HTTP server on port {port}: {e}")
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
