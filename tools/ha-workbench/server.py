"""HA Ingress workbench. Builds directly from a read-only shared Git checkout.

The app never exports/imports a project, flashes a device or writes source files.
Only declared profiles can run. Artifacts and per-profile caches live in /data.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time
from urllib.parse import parse_qs, unquote, urlsplit

from PIL import Image
import yaml

APP = Path(__file__).resolve().parent
DATA = Path(os.environ.get("FORMAPANEL_DATA", "/data"))
OPTIONS = DATA / "options.json"
WORKSPACE = Path(os.environ.get("FORMAPANEL_WORKSPACE", json.loads(OPTIONS.read_text()).get("workspace")
                 if OPTIONS.exists() else "/homeassistant/esphome/formapanel-rh01")).resolve()
DATA.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()
JOB = {"status": "idle"}
FINGERPRINT_CACHE = {}


def inside(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Path is outside the selected workspace")
    return path


def profiles():
    result = json.loads((WORKSPACE / "config/workbench-targets.json").read_text("utf-8"))["profiles"]
    ids = set()
    for item in result:
        name = item["id"]
        if not re.fullmatch(r"[a-z0-9_-]{1,48}", name) or name in ids:
            raise ValueError("Invalid or duplicate profile ID")
        ids.add(name)
        for key in ("firmware", "preview"):
            path = inside(WORKSPACE, item[key])
            if path.suffix != ".yaml" or not path.is_file():
                raise ValueError(f"Missing {key} configuration for {name}")
    return result


def fingerprint():
    digest = hashlib.sha256()
    for folder in ("firmware", "assets", "config"):
        for path in sorted((WORKSPACE / folder).rglob("*")):
            relative = path.relative_to(WORKSPACE)
            if (not path.is_file() or any(p in (".git", ".esphome", "build", "__pycache__") for p in relative.parts)
                    or "secret" in path.name.lower() or path.suffix.lower() not in
                    (".yaml", ".yml", ".png", ".svg", ".ttf", ".json", ".h", ".cpp", ".c")):
                continue
            stat = path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            cached = FINGERPRINT_CACHE.get(path)
            if cached is None or cached[0] != signature:
                cached = (signature, hashlib.sha256(path.read_bytes()).digest())
                FINGERPRINT_CACHE[path] = cached
            digest.update(relative.as_posix().encode())
            digest.update(cached[1])
    return digest.hexdigest()


def git_info():
    def git(*args):
        try:
            return subprocess.check_output(["git", "-c", f"safe.directory={WORKSPACE}", "-C", str(WORKSPACE), *args],
                                           stderr=subprocess.DEVNULL, text=True, timeout=5,
                                           env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    return {"branch": git("branch", "--show-current"), "commit": git("rev-parse", "--short", "HEAD"),
            "dirty": bool(git("status", "--porcelain"))}


def secret_values():
    values = []
    for path in WORKSPACE.glob("**/*secrets*.yaml"):
        if ".git" in path.parts or ".esphome" in path.parts:
            continue
        try:
            payload = yaml.safe_load(path.read_text("utf-8"))
            if isinstance(payload, dict):
                values += [str(v) for v in payload.values() if isinstance(v, (str, int)) and len(str(v)) > 3]
        except (OSError, yaml.YAMLError):
            pass
    return sorted(values, key=len, reverse=True)


def log_line(job, line, secrets):
    # Drop ANSI codes and never retain expanded credentials in build output.
    line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line)
    for value in secrets:
        line = line.replace(value, "[REDACTED]")
    with LOCK:
        job["log"] = (job.get("log", "") + line)[-80000:]
    with (DATA / "jobs" / job["id"] / "build.log").open("a", encoding="utf-8") as output:
        output.write(line)


def command(job, argv, env, secrets, timeout=1800, marker=None, cwd=None):
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               errors="replace", env=env, cwd=cwd, start_new_session=True)
    expired = threading.Event()
    def terminate():
        expired.set()
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    timer = threading.Timer(timeout, terminate)
    timer.start()
    matched = False
    try:
        for line in process.stdout:
            log_line(job, line, secrets)
            if marker and marker in line:
                matched = True
                os.killpg(process.pid, signal.SIGTERM)
                break
        try:
            code = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait()
        if expired.is_set():
            raise RuntimeError("Build or render timed out")
        if marker and not matched:
            raise RuntimeError("Renderer stopped before completing the snapshots")
        if not marker and code:
            raise RuntimeError(f"Command failed (exit {code}); see the build log")
    finally:
        timer.cancel()
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def run_job(job, profile):
    folder = DATA / "jobs" / job["id"]
    folder.mkdir(parents=True, exist_ok=True)
    try:
        job["source_fingerprint"] = fingerprint()
        secrets = secret_values()
        native = job["kind"] == "preview"
        entry = inside(WORKSPACE, profile["preview" if native else "firmware"])
        build = DATA / "build" / ("preview-" if native else "firmware-") / profile["id"]
        # ESPHome stores compatibility metadata below its data directory. A
        # per-job config/data path looks like a first build and wipes the shared
        # build tree. Keep both identities stable; only artifacts vary by job.
        wrapper = DATA / "configs" / f"{job['kind']}-{profile['id']}.yaml"
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        esphome_data = DATA / "esphome" / job["kind"] / profile["id"]
        esphome_data.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(yaml.safe_dump({
            "substitutions": {"formapanel_asset_dir": str(WORKSPACE / "assets"),
                              "preview_build_path": str(build), "formapanel_build_path": str(build)},
            "esphome": {"build_path": str(build)},
            "packages": {"workspace": "INCLUDE_ENTRY"}}, sort_keys=False).replace(
                "workspace: INCLUDE_ENTRY", "workspace: !include " + json.dumps(str(entry))), "utf-8")
        env = os.environ.copy()
        env.pop("ESPHOME_IS_HA_ADDON", None)
        env["ESPHOME_DATA_DIR"] = str(esphome_data)
        env["ESPHOME_ESP_IDF_PREFIX"] = "/data/cache/idf"
        env["ESPHOME_HOST_PREFIX"] = "/data/cache/host"
        env["ESPHOME_SNAPSHOT_DIR"] = str(folder / "snapshots")
        # Config validation stdout expands the configuration, so discard it on
        # success and redact it before returning any validation errors.
        check = subprocess.run(["esphome", "config", str(wrapper)], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, env=env, timeout=180)
        if check.returncode:
            log_line(job, check.stdout, secrets)
            raise RuntimeError("ESPHome configuration validation failed")
        log_line(job, "ESPHome configuration: PASS\n", secrets)
        if job["kind"] != "validate":
            command(job, ["esphome", "compile", str(wrapper)], env, secrets)
        captures, artifacts = [], []
        if native:
            program = build / "build" / "firmware"
            if not program.is_file():
                choices = [p for p in build.rglob("program") if p.is_file()]
                choices += [p for p in build.rglob("firmware") if p.is_file() and os.access(p, os.X_OK)]
                if len(choices) != 1:
                    raise RuntimeError("Cannot identify the compiled native executable")
                program = choices[0]
            # Capture paths are unique per job; snapshot.take never overwrites.
            (folder / "snapshots").mkdir(exist_ok=True)
            command(job, [str(program)], env, secrets, timeout=90,
                    marker="RH01_NATIVE_PREVIEW_COMPLETE", cwd=folder)
            for bmp in sorted((folder / "snapshots").rglob("*.bmp")):
                png = folder / (bmp.stem + ".png")
                with Image.open(bmp) as original:
                    original.convert("RGB").save(png, optimize=True)
                captures.append({"name": bmp.stem, "url": f"files/{job['id']}/{png.name}"})
            if len(captures) < 2:
                raise RuntimeError("Renderer did not produce both lamp states")
        elif job["kind"] == "firmware":
            for source in sorted(build.rglob("firmware*.bin")):
                if source.name not in ("firmware.factory.bin", "firmware.ota.bin"):
                    continue
                output = folder / source.name
                output.write_bytes(source.read_bytes())
                artifacts.append({"name": source.name, "url": f"files/{job['id']}/{source.name}",
                                  "bytes": output.stat().st_size,
                                  "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
            if not artifacts:
                raise RuntimeError("Compiler produced no Factory/OTA images")
        result = {"captures": captures, "artifacts": artifacts,
                  "source_fingerprint": job["source_fingerprint"], "job_id": job["id"]}
        result_path = DATA / f"result-{profile['id']}-{job['kind']}.json"
        temporary = result_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(result), "utf-8")
        temporary.replace(result_path)
        with LOCK:
            job["status"] = "complete"
            job["finished_at"] = time.time()
    except Exception as error:
        with LOCK:
            job["status"] = "failed"
            job["error"] = str(error)
        log_line(job, "\n" + str(error) + "\n", locals().get("secrets", []))
    finally:
        (folder / "job.json").write_text(json.dumps(job), "utf-8")


def state(profile_id):
    available = profiles()
    if profile_id not in {p["id"] for p in available}:
        profile_id = available[0]["id"]
    result = {}
    for kind in ("preview", "firmware"):
        path = DATA / f"result-{profile_id}-{kind}.json"
        if path.exists():
            result[kind] = json.loads(path.read_text("utf-8"))
    current = fingerprint()
    with LOCK:
        job = dict(JOB)
    preview = result.get("preview", {})
    return {"profiles": [{"id": p["id"], "label": p["label"]} for p in available],
            "profile": profile_id, "git": git_info(), "job": job,
            "captures": preview.get("captures", []), "artifacts": result.get("firmware", {}).get("artifacts", []),
            "source_fingerprint": current, "result_fingerprint": preview.get("source_fingerprint"),
            "captures_stale": bool(preview) and current != preview.get("source_fingerprint"),
            "links": {"editor": "/a0d7b954_vscode", "builder": "/5c53de3b_esphome"}}


class Handler(http.server.BaseHTTPRequestHandler):
    def allowed(self):
        # Ingress handles authentication. A separate host port is never exposed.
        if self.client_address[0] not in ("172.30.32.2", "127.0.0.1", "::1"):
            self.send_error(403)
            return False
        return True

    def reply(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed():
            return
        request = urlsplit(self.path)
        try:
            if request.path == "/api/state":
                self.reply(200, state(parse_qs(request.query).get("profile", [""])[0]))
                return
            if request.path.startswith("/files/"):
                parts = unquote(request.path).split("/")
                if len(parts) != 4 or not re.fullmatch(r"[a-z0-9_-]+", parts[2]):
                    raise ValueError("Invalid artifact URL")
                if not re.fullmatch(r"[a-zA-Z0-9_.-]+\.(?:png|bin)", parts[3]):
                    raise ValueError("Invalid artifact type")
                path = inside(DATA / "jobs", parts[2] + "/" + parts[3])
            else:
                path = inside(APP / "web", request.path.lstrip("/") or "index.html")
                if path.suffix not in (".html", ".js", ".css", ".svg"):
                    raise ValueError("Unsupported resource")
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png" if path.suffix == ".png" else
                             "text/html; charset=utf-8" if path.suffix == ".html" else
                             "text/javascript" if path.suffix == ".js" else
                             "text/css" if path.suffix == ".css" else "application/octet-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, FileNotFoundError) as error:
            self.reply(404, {"error": str(error)})
        except Exception as error:
            self.reply(500, {"error": str(error)})

    def do_POST(self):
        global JOB
        if not self.allowed():
            return
        try:
            if urlsplit(self.path).path != "/api/jobs":
                self.reply(404, {"error": "Unknown endpoint"})
                return
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size < 4096:
                raise ValueError("Invalid job request")
            payload = json.loads(self.rfile.read(size))
            kind, profile_id = payload.get("kind"), payload.get("profile")
            if kind not in ("preview", "firmware", "validate"):
                raise ValueError("Unknown job kind")
            profile = next((p for p in profiles() if p["id"] == profile_id), None)
            if profile is None:
                raise ValueError("Unknown profile")
            with LOCK:
                if JOB.get("status") == "running":
                    self.reply(409, {"error": "A build is already running"})
                    return
                JOB = {"id": f"{int(time.time() * 1000)}-{profile_id}", "kind": kind,
                       "profile": profile_id, "status": "running", "started_at": time.time(), "log": ""}
                job = JOB
            threading.Thread(target=run_job, args=(job, profile), daemon=True).start()
            self.reply(202, {"job": job})
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.reply(400, {"error": str(error)})
        except Exception as error:
            self.reply(500, {"error": str(error)})


if __name__ == "__main__":
    print(f"FormaPanel Workshop: {WORKSPACE}", flush=True)
    http.server.ThreadingHTTPServer(("0.0.0.0", 8099), Handler).serve_forever()
