"""Boundaries that matter for the authenticated build service."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.workspace = self.directory / "repo"
        (self.workspace / "config").mkdir(parents=True)
        (self.workspace / "firmware").mkdir()
        (self.workspace / "assets").mkdir()
        (self.workspace / "firmware/entry.yaml").write_text("host:\n", "utf-8")
        self.manifest = {"profiles": [{"id": "demo", "label": "Demo", "firmware": "firmware/entry.yaml",
                                      "preview": "firmware/entry.yaml"}]}
        self.save_manifest()
        with patch.dict(os.environ, {"FORMAPANEL_WORKSPACE": str(self.workspace),
                                     "FORMAPANEL_DATA": str(self.directory / "data")}):
            spec = importlib.util.spec_from_file_location("workbench_test_server", ROOT / "tools/ha-workbench/server.py")
            self.server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.server)

    def save_manifest(self):
        (self.workspace / "config/workbench-targets.json").write_text(json.dumps(self.manifest), "utf-8")

    def test_target_cannot_escape_workspace(self):
        self.assertEqual(self.server.profiles()[0]["id"], "demo")
        self.manifest["profiles"][0]["preview"] = "../private.yaml"
        self.save_manifest()
        with self.assertRaises(ValueError):
            self.server.profiles()
        with self.assertRaises(ValueError):
            self.server.inside(self.workspace, "../../private.bin")

    def test_source_change_marks_preview_stale_but_secrets_are_not_hashed(self):
        first = self.server.fingerprint()
        secret = self.workspace / "firmware/secrets.yaml"
        secret.write_text("wifi_password: private\n", "utf-8")
        self.assertEqual(first, self.server.fingerprint())
        (self.workspace / "firmware/entry.yaml").write_text("host:\n# edited in browser\n", "utf-8")
        self.assertNotEqual(first, self.server.fingerprint())

    def test_private_values_never_enter_saved_build_log(self):
        folder = self.server.DATA / "jobs/example"
        folder.mkdir(parents=True)
        job = {"id": "example", "log": ""}
        self.server.log_line(job, "\x1b[31mwifi_password: long-private-value\x1b[0m\n", ["long-private-value"])
        self.assertNotIn("long-private-value", job["log"])
        self.assertNotIn("long-private-value", (folder / "build.log").read_text("utf-8"))
        self.assertIn("[REDACTED]", job["log"])
        self.assertNotIn("\x1b", job["log"])

    def test_build_identity_persists_between_jobs_and_isolates_targets(self):
        configurations = []

        def validate(argv, **kwargs):
            configurations.append((Path(argv[-1]), kwargs["env"].copy()))
            return SimpleNamespace(returncode=0, stdout="")

        def compile_or_capture(job, argv, env, secrets, **kwargs):
            if argv[0] == "esphome":
                build = self.server.DATA / "build" / (
                    "preview-" if job["kind"] == "preview" else "firmware-") / job["profile"]
                build.mkdir(parents=True, exist_ok=True)
                if job["kind"] == "preview":
                    (build / "build").mkdir(exist_ok=True)
                    (build / "build/firmware").write_bytes(b"test executable")
                else:
                    (build / "firmware.factory.bin").write_bytes(b"test artifact")
            else:
                for name in ("rh01-on.bmp", "rh01-off.bmp"):
                    self.server.Image.new("RGB", (1, 1)).save(Path(env["ESPHOME_SNAPSHOT_DIR"]) / name)

        jobs = [("preview", "living"), ("preview", "living"),
                ("preview", "bedroom"), ("firmware", "living"), ("validate", "living")]
        with patch.object(self.server.subprocess, "run", side_effect=validate), \
                patch.object(self.server, "command", side_effect=compile_or_capture):
            for index, (kind, profile_id) in enumerate(jobs):
                job = {"id": f"test-{index}", "kind": kind, "profile": profile_id,
                       "status": "running", "log": ""}
                profile = {**self.manifest["profiles"][0], "id": profile_id}
                self.server.run_job(job, profile)
                self.assertEqual(job["status"], "complete", job.get("error"))
                data = Path(configurations[-1][1]["ESPHOME_DATA_DIR"])
                marker = data / "retained-metadata"
                if index == 1:
                    self.assertEqual(marker.read_text("utf-8"), "first job")
                marker.write_text("first job", "utf-8")

        self.assertEqual(configurations[0][0], configurations[1][0])
        self.assertEqual(configurations[0][1]["ESPHOME_DATA_DIR"], configurations[1][1]["ESPHOME_DATA_DIR"])
        isolated = [configurations[index] for index in (0, 2, 3, 4)]
        self.assertEqual(len({path for path, _ in isolated}), 4)
        self.assertEqual(len({env["ESPHOME_DATA_DIR"] for _, env in isolated}), 4)
        self.assertEqual(len({env["ESPHOME_SNAPSHOT_DIR"] for _, env in configurations}), len(jobs))
        self.assertTrue(all("ESPHOME_IS_HA_ADDON" not in env for _, env in configurations))


if __name__ == "__main__":
    unittest.main()
