import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tabtelly"
COMPAT_CLI = ROOT / "tabcast"


FAKE_SERVER = r'''
import json
import os
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ["TABCAST_PORT"])
RUNTIME = Path(os.environ["TABCAST_RUNTIME_DIR"])
INSTANCE = os.environ.get("FAKE_INSTANCE", "test-instance")
ADMIN = "admin-secret"
SENDER = "sender-secret"

RUNTIME.mkdir(parents=True, exist_ok=True)
session = RUNTIME / "session.json"
session.write_text(json.dumps({
    "adminToken": ADMIN,
    "senderToken": SENDER,
    "pairCode": "123456",
    "instance": INSTANCE,
    "pid": os.getpid(),
    "port": PORT,
}))
try:
    session.chmod(0o600)
except OSError:
    pass

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self.send_json({
                "app": "tabcast", "version": "0.1.0",
                "instance": INSTANCE, "pid": os.getpid(),
            })
        if self.path == "/status":
            if self.headers.get("X-Tabcast-Token") != ADMIN:
                return self.send_json({"error": "unauthorized"}, 401)
            return self.send_json({
                "receiverUrl": f"http://127.0.0.1:{PORT}/",
                "senderUrl": f"http://localhost:{PORT}/send",
                "pairCode": "123456",
                "tv": {"online": False},
                "sender": {"online": False},
            })
        return self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/shutdown" and self.headers.get("X-Tabcast-Token") == ADMIN:
            if self.headers.get("Content-Type") != "application/json":
                return self.send_json({"error": "json required"}, 415)
            self.send_json({"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        return self.send_json({"error": "unauthorized"}, 401)

ThreadingHTTPServer((os.environ.get("TABCAST_BIND", "127.0.0.1"), PORT), Handler).serve_forever()
'''


OTHER_SERVER = r'''
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        value = json.loads(os.environ["HEALTH_JSON"])
        body = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        self.send_response(500)
        self.send_header("Content-Length", "0")
        self.end_headers()

ThreadingHTTPServer(("127.0.0.1", int(os.environ["PORT"])), Handler).serve_forever()
'''


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_http(port):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError(f"server on port {port} did not start")


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tabcast cli ")
        self.project = Path(self.temp.name) / "project with spaces"
        self.project.mkdir()
        shutil.copy2(CLI if CLI.exists() else COMPAT_CLI, self.project / "tabtelly")
        shutil.copy2(COMPAT_CLI, self.project / "tabcast")
        (self.project / "server.py").write_text(textwrap.dedent(FAKE_SERVER))
        self.processes = []

    def tearDown(self):
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
        self.temp.cleanup()

    def run_cli(self, *args, port=None, runtime=None, timeout=10):
        env = os.environ.copy()
        env["TABCAST_PORT"] = str(port or free_port())
        if runtime is not None:
            env["TABCAST_RUNTIME_DIR"] = str(runtime)
        return subprocess.run(
            [sys.executable, str(self.project / "tabtelly"), *args],
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )

    def start_other_server(self, port, health):
        source = self.project / f"other-{port}.py"
        source.write_text(textwrap.dedent(OTHER_SERVER))
        env = os.environ.copy()
        env.update(PORT=str(port), HEALTH_JSON=json.dumps(health))
        proc = subprocess.Popen(
            [sys.executable, str(source)], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.processes.append(proc)
        wait_for_http(port)
        return proc

    def test_version_and_help(self):
        version = self.run_cli("--version")
        self.assertEqual(version.returncode, 0, version.stderr)
        self.assertEqual(version.stdout.strip(), "TabTelly 0.1.0")

        help_result = self.run_cli("--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for command in ("start", "stop", "restart", "status", "log", "doctor"):
            self.assertIn(command, help_result.stdout)

    def test_start_status_and_stop_from_path_with_spaces(self):
        port = free_port()
        runtime = self.project / "state with spaces"

        started = self.run_cli("start", "--no-open", port=port, runtime=runtime)
        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)
        self.assertIn("TabTelly server started", started.stdout)
        self.assertIn(f"http://127.0.0.1:{port}/", started.stdout)
        self.assertIn("Pairing code: 123456", started.stdout)
        self.assertIn("loopback", started.stdout.lower())
        self.assertTrue((runtime / "session.json").exists())

        status = self.run_cli("status", port=port, runtime=runtime)
        self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
        self.assertIn("Receiver URL", status.stdout)
        self.assertIn("Pair code", status.stdout)

        first_pid = json.loads((runtime / "session.json").read_text())["pid"]
        restarted = self.run_cli("restart", "--no-open", port=port, runtime=runtime)
        self.assertEqual(restarted.returncode, 0, restarted.stderr + restarted.stdout)
        self.assertIn("TabTelly stopped", restarted.stdout)
        self.assertIn("TabTelly server started", restarted.stdout)
        second_pid = json.loads((runtime / "session.json").read_text())["pid"]
        self.assertNotEqual(first_pid, second_pid)

        stopped = self.run_cli("stop", port=port, runtime=runtime)
        self.assertEqual(stopped.returncode, 0, stopped.stderr + stopped.stdout)
        self.assertIn("TabTelly stopped", stopped.stdout)

        stopped_again = self.run_cli("stop", port=port, runtime=runtime)
        self.assertEqual(stopped_again.returncode, 0, stopped_again.stderr)
        self.assertIn("not running", stopped_again.stdout)

    def test_default_runtime_is_private_and_port_specific(self):
        first, second = free_port(), free_port()
        a = self.run_cli("start", "--no-open", port=first)
        b = self.run_cli("start", "--no-open", port=second)
        self.assertEqual(a.returncode, 0, a.stderr + a.stdout)
        self.assertEqual(b.returncode, 0, b.stderr + b.stdout)
        first_runtime = self.project / ".run" / str(first)
        second_runtime = self.project / ".run" / str(second)
        self.assertTrue((first_runtime / "session.json").exists())
        self.assertTrue((second_runtime / "session.json").exists())
        if os.name == "posix":
            self.assertEqual(first_runtime.stat().st_mode & 0o777, 0o700)

        self.assertEqual(self.run_cli("stop", port=first).returncode, 0)
        second_status = self.run_cli("status", port=second)
        self.assertEqual(second_status.returncode, 0, second_status.stderr + second_status.stdout)
        self.assertEqual(self.run_cli("stop", port=second).returncode, 0)

    def test_occupied_port_is_not_killed(self):
        port = free_port()
        other = self.start_other_server(port, {"app": "something-else", "pid": 1})

        result = self.run_cli("start", "--no-open", port=port)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already in use", result.stderr)
        self.assertIsNone(other.poll())

    def test_stale_or_reused_pid_is_not_killed(self):
        port = free_port()
        other = self.start_other_server(port, {
            "app": "tabcast", "version": "0.1.0",
            "instance": "new-instance", "pid": 999999,
        })
        runtime = self.project / "stale"
        runtime.mkdir(mode=0o700)
        (runtime / "session.json").write_text(json.dumps({
            "adminToken": "old-secret",
            "senderToken": "old-sender",
            "pairCode": "000000",
            "instance": "old-instance",
            "pid": other.pid,
            "port": port,
        }))

        result = self.run_cli("stop", port=port, runtime=runtime)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("different TabTelly instance", result.stderr)
        self.assertIsNone(other.poll())

    def test_doctor_reports_configuration_without_external_tools(self):
        port = free_port()
        runtime = self.project / "doctor-state"
        result = self.run_cli("doctor", port=port, runtime=runtime)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Python", result.stdout)
        self.assertIn("server.py", result.stdout)
        self.assertIn(str(port), result.stdout)
        self.assertIn("available", result.stdout)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_runtime_symlink_is_refused(self):
        target = self.project / "runtime target"
        target.mkdir()
        runtime = self.project / "runtime link"
        runtime.symlink_to(target, target_is_directory=True)

        result = self.run_cli("doctor", port=free_port(), runtime=runtime)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symbolic link", result.stderr.lower())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_log_symlink_is_refused_without_touching_target(self):
        port = free_port()
        runtime = self.project / "log state"
        runtime.mkdir()
        target = self.project / "unrelated file"
        target.write_text("do not modify")
        original_mode = target.stat().st_mode & 0o777
        (runtime / "server.log").symlink_to(target)

        result = self.run_cli("start", "--no-open", port=port, runtime=runtime)
        if result.returncode == 0:
            self.run_cli("stop", port=port, runtime=runtime)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symbolic link", result.stderr.lower())
        self.assertEqual(target.read_text(), "do not modify")
        if os.name == "posix":
            self.assertEqual(target.stat().st_mode & 0o777, original_mode)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_session_symlink_is_refused_without_overwriting_target(self):
        port = free_port()
        runtime = self.project / "session state"
        runtime.mkdir()
        target = self.project / "unrelated session file"
        target.write_text("do not modify")
        (runtime / "session.json").symlink_to(target)

        result = self.run_cli("start", "--no-open", port=port, runtime=runtime)
        if result.returncode == 0:
            self.run_cli("stop", port=port, runtime=runtime)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symbolic link", result.stderr.lower())
        self.assertEqual(target.read_text(), "do not modify")

    def test_doctor_rejects_unsafe_bind_and_invalid_lan_ip(self):
        env = os.environ.copy()
        env.update(TABTELLY_PORT=str(free_port()), TABTELLY_BIND="192.0.2.5")
        bind = subprocess.run(
            [sys.executable, str(self.project / "tabtelly"), "doctor"],
            cwd=self.project, env=env, text=True, capture_output=True,
        )
        self.assertNotEqual(bind.returncode, 0)
        self.assertIn("TABTELLY_BIND", bind.stderr)

        env.update(TABTELLY_BIND="127.0.0.1", TABTELLY_LAN_IP="not-an-ip")
        lan_ip = subprocess.run(
            [sys.executable, str(self.project / "tabtelly"), "doctor"],
            cwd=self.project, env=env, text=True, capture_output=True,
        )
        self.assertNotEqual(lan_ip.returncode, 0)
        self.assertIn("TABTELLY_LAN_IP", lan_ip.stderr)

    def test_tabcast_compatibility_launcher(self):
        env = os.environ.copy()
        env["TABTELLY_PORT"] = str(free_port())
        result = subprocess.run(
            [sys.executable, str(self.project / "tabcast"), "--version"],
            cwd=self.project, env=env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "TabTelly 0.1.0")

    def test_tabtelly_environment_names_take_precedence(self):
        primary_port, legacy_port = free_port(), free_port()
        primary_runtime = self.project / "primary runtime"
        legacy_runtime = self.project / "legacy runtime"
        env = os.environ.copy()
        env.update({
            "TABTELLY_PORT": str(primary_port),
            "TABCAST_PORT": str(legacy_port),
            "TABTELLY_RUNTIME_DIR": str(primary_runtime),
            "TABCAST_RUNTIME_DIR": str(legacy_runtime),
        })
        result = subprocess.run(
            [sys.executable, str(self.project / "tabtelly"), "doctor"],
            cwd=self.project, env=env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn(f"Port {primary_port}", result.stdout)
        self.assertIn(str(primary_runtime), result.stdout)
        self.assertFalse(legacy_runtime.exists())


class RealServerIntegrationTest(unittest.TestCase):
    def test_launcher_manages_the_real_server_contract(self):
        with tempfile.TemporaryDirectory(prefix="tabtelly real ") as directory:
            project = Path(directory) / "real project with spaces"
            project.mkdir()
            shutil.copy2(CLI, project / "tabtelly")
            shutil.copy2(ROOT / "server.py", project / "server.py")
            shutil.copytree(ROOT / "web", project / "web")
            port = free_port()
            runtime = project / "private runtime"
            env = os.environ.copy()
            env.update(TABTELLY_PORT=str(port), TABTELLY_RUNTIME_DIR=str(runtime))

            def run(*args):
                return subprocess.run(
                    [sys.executable, str(project / "tabtelly"), *args],
                    cwd=project, env=env, text=True, capture_output=True, timeout=10,
                )

            try:
                started = run("start", "--no-open")
                self.assertEqual(started.returncode, 0, started.stderr + started.stdout)
                status = run("status")
                self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
                self.assertIn(f"http://localhost:{port}/send", status.stdout)
            finally:
                stopped = run("stop")
            self.assertEqual(stopped.returncode, 0, stopped.stderr + stopped.stdout)


if __name__ == "__main__":
    unittest.main()
