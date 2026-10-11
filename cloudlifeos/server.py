"""Loopback-only reader around the existing Foundry monitor, with explicit provenance."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .evidence import project

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
CORE = LOCAL / "core-brain"
MONITOR_DIR = CORE / "tools/agent-process-monitor"


def load_source():
    manifest = json.loads((LOCAL / "source.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        if hashlib.sha256((CORE / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Source fingerprint mismatch; rerun bootstrap and restart.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=CORE, text=True).strip()
    if revision != manifest["revision"]:
        raise RuntimeError("Source revision mismatch; rerun bootstrap and restart.")
    if not source_unchanged(manifest):
        raise RuntimeError("Snapshot integrity mismatch; rerun bootstrap and restart.")
    spec = importlib.util.spec_from_file_location("lifeos_existing_monitor", MONITOR_DIR / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return manifest, module


def source_unchanged(manifest):
    try:
        if json.loads((LOCAL / "source.json").read_text(encoding="utf-8")) != manifest:
            return False
        for name, digest in manifest["files"].items():
            if hashlib.sha256((CORE / name).read_bytes()).hexdigest() != digest:
                return False
            if name.startswith("runtime/status/"):
                if hashlib.sha256((LOCAL / "snapshots" / Path(name).name).read_bytes()).hexdigest() != digest:
                    return False
        return True
    except (OSError, ValueError):
        return False


def health(manifest, now=None):
    now = now or datetime.now(timezone.utc)
    github = {
        "id": "github", "label": "GitHub • Core Brain", "mode": "live",
        "observed_at": manifest["observed_at"], "ttl_seconds": 300,
        "connected": True, "authenticated": None, "admitted": True, "verified_working": True,
        "scope": "อ่าน main ของ LifeOS-Foundry ผ่าน Git เท่านั้น",
        "source": f"sangkeat/LifeOS-Foundry@{manifest['revision']}",
        "limitation": "ไม่พิสูจน์สิทธิ์ API, push, repository อื่น หรือปลั๊กอิน GitHub",
        "recovery": "ตรวจ main ใหม่ด้วย python3 scripts/bootstrap.py แล้วเริ่ม server ใหม่",
    }
    cloud = {
        "id": "cloud", "label": "Cloud • เครื่องพัฒนานี้", "mode": "live", "observed_at": now.isoformat(),
        "ttl_seconds": 15, "connected": True, "authenticated": None, "admitted": True,
        "verified_working": True, "scope": "server ตอบคำขออ่าน health ในเครื่องนี้",
        "source": "คำขอ /api/health ครั้งนี้", "limitation": "ไม่พิสูจน์ hosting ถาวรหรือ connector อื่น",
        "recovery": "เริ่ม python3 -m cloudlifeos.server ใน checkout ที่ได้รับอนุญาต",
    }
    channels = [cloud, github]
    for identifier, label in [("localagent", "LocalAgent / PiDzPC"), ("drive", "Google Drive"), ("wiki", "LifeOsWiki")]:
        channels.append({
            "id": identifier, "label": label, "mode": "snapshot", "observed_at": None, "ttl_seconds": 300,
            "connected": None, "authenticated": None, "admitted": None, "verified_working": None,
            "scope": "ยังไม่มีเครื่องมือที่เรียกได้ใน Cloud adapter นี้", "source": "ไม่มีหลักฐาน runtime สด",
            "limitation": "ไม่ได้แปลว่าระบบนั้นล่ม; รายงานเดิมไม่พิสูจน์ความพร้อมในเซสชันนี้",
            "recovery": None,
        })
    # Refreshing source while this process runs requires restart, not adoption by implication.
    changed = not source_unchanged(manifest)
    if changed:
        github.update(mode="snapshot", limitation="source เปลี่ยนหลังเริ่ม process; ต้องเริ่ม server ใหม่ก่อนใช้งาน", recovery="หยุดเฉพาะ server นี้ แล้วเริ่มใหม่")
    return {
        "schema_version": 1, "observed_at": now.isoformat(), "channels": [project(c, now) for c in channels],
        "source": {k: manifest[k] for k in ["repository", "branch", "revision", "observed_at"]},
        "source_changed_since_start": changed,
        "mission": {"phase": "cloud-adapter", "status": "partial", "base_v08": "not_retrieved",
                    "next_action": "อ่านไฟล์ฐาน v0.8 ผ่าน Operator ที่พร้อมจริง แล้วเทียบฟังก์ชันก่อนพัฒนา Owner Cockpit"},
        "snapshot_notice": "Monitor เดิมด้านล่างเป็นข้อมูลจาก repository snapshot; ไม่ใช่ runtime เครื่องเจ้าของ",
    }


def make_handler(manifest, monitor):
    # Load these bytes once; never execute newly edited upstream HTML/JS by accident.
    assets = {"/monitor": ((MONITOR_DIR / "dashboard.html").read_bytes(), "text/html; charset=utf-8"),
              "/owner-status.js": ((MONITOR_DIR / "owner-status.js").read_bytes(), "application/javascript; charset=utf-8")}
    snapshots = {}
    for name in ["goal-registry", "mission-state", "session-plan"]:
        snapshots[name] = json.loads((LOCAL / "snapshots" / f"{name}.json").read_text(encoding="utf-8"))

    class Handler(monitor.MonitorHandler):
        status_dir = LOCAL / "status"
        signal_dir = LOCAL / "signals"

        def log_message(self, *_):
            pass

        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'none'")
            super().end_headers()

        def send_json(self, payload, status=200):
            if isinstance(payload, dict) and "agents" in payload:
                # Serving a cached local status is not a live LocalAgent connection.
                for connection in payload.get("connections", {}).values():
                    connection.update(state="unknown", is_live=False, detail="ข้อมูล snapshot จาก repository; ไม่ได้ตรวจ runtime สดในเซสชันนี้")
                payload["projection"] = {"mode": "snapshot", "source_revision": manifest["revision"], "runtime_verified": False}
            super().send_json(payload, status)

        def safe_origin(self):
            host = self.headers.get("Host", "")
            port = self.server.server_port
            allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if host not in allowed:
                return False
            origin = self.headers.get("Origin")
            return origin is None or origin in {f"http://{h}" for h in allowed}

        def do_GET(self):
            if not self.safe_origin():
                self.send_json({"error": "origin not admitted"}, 403)
                return
            route = urlsplit(self.path).path
            source_routes = {"/monitor", "/owner-status.js", "/api/status", "/api/source-summary"}
            if route in source_routes and not source_unchanged(manifest):
                self.send_json({"error": "source changed; restart required"}, 503)
                return
            static = {"/": (ROOT / "web/index.html", "text/html; charset=utf-8"),
                      "/app.js": (ROOT / "web/app.js", "application/javascript; charset=utf-8"),
                      "/app.css": (ROOT / "web/app.css", "text/css; charset=utf-8")}
            if route in static:
                self.send_file(*static[route])
            elif route in assets:
                body, content_type = assets[route]
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif route == "/api/health":
                self.send_json(health(manifest))
            elif route == "/api/source-summary":
                result = {}
                for name in ["goal-registry", "mission-state", "session-plan"]:
                    data = snapshots[name]
                    result[name] = {"mode": "snapshot", "record_updated_at": data.get("updated_at"), "source_revision": manifest["revision"]}
                self.send_json(result)
            elif route == "/api/status":
                # These derived files are only for the unchanged existing renderer.
                # Reject mutable copies with different bytes rather than mislabeling their revision.
                for name in snapshots:
                    digest = manifest["files"][f"runtime/status/{name}.json"]
                    try:
                        actual = hashlib.sha256((self.status_dir / f"{name}.json").read_bytes()).hexdigest()
                    except OSError:
                        actual = None
                    if actual != digest:
                        self.send_json({"error": "snapshot changed; restart required"}, 503)
                        return
                super().do_GET()
            else:
                self.send_json({"error": "not found"}, 404)

        def do_POST(self):
            self.send_json({"error": "read-only"}, 405)

        do_PUT = do_DELETE = do_PATCH = do_POST

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Read-only LifeOS Cloud development adapter; no production hosting")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    manifest, monitor = load_source()
    (LOCAL / "status").mkdir(exist_ok=True)
    # Existing monitor functions render the existing authoritative snapshot files.
    for name in ["goal-registry.json", "mission-state.json", "session-plan.json"]:
        (LOCAL / "status" / name).write_bytes((LOCAL / "snapshots" / name).read_bytes())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(manifest, monitor))
    print(f"Cloud adapter ready on loopback port {server.server_port}; no hosted URL or LocalAgent admission.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
