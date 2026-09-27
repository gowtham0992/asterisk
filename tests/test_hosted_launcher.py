"""Exercise the real launcher with a fake interpreter; no server or provider calls."""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def launch(tmp_path, **overrides):
    scripts = tmp_path / "scripts"
    scripts.mkdir(exist_ok=True)
    script = scripts / "start_hosted.sh"
    script.write_bytes((ROOT / "scripts/start_hosted.sh").read_bytes())
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.write_text('#!/bin/sh\nprintf "public=%s entity=%s\\n" "$ASTERISK_PUBLIC" "$ASTERISK_ENTITY_ONLY"\nprintf "%s\\n" "$@"\n')
    interpreter.chmod(0o755)
    env = {"PATH": os.environ["PATH"], "ASTERISK_ALLOWED_HOSTS": "preview.example.org",
           "ASTERISK_PREVIEW_PASSWORD": "fictional-preview-password-only",
           "ASTERISK_DB": str(tmp_path / "preview.sqlite"),
           "NEBIUS_API_KEY": "fictional-key", "NEBIUS_PROJECT_ID": "fictional-project"}
    env.update(overrides)
    return subprocess.run(["sh", str(script)], env=env, text=True, capture_output=True)


def test_ladder_launch_requires_no_legacy_image(tmp_path):
    result = launch(tmp_path, ASTERISK_HOSTED_WORKFLOW="ladder", PORT="8799")
    assert result.returncode == 0, result.stderr
    assert "public=1 entity=1" in result.stdout
    assert "app.main:app" in result.stdout
    assert "8799" in result.stdout
    assert result.stdout.endswith("--workers\n1\n")


def test_legacy_default_still_requires_image_and_driver(tmp_path):
    result = launch(tmp_path)
    assert result.returncode != 0 and "ASTERISK_PROBE_IMAGE" in result.stderr
    result = launch(tmp_path, ASTERISK_PROBE_IMAGE="fictional-image")
    assert result.returncode != 0 and "ASTERISK_PROBE_DRIVER_SHA256" in result.stderr
    result = launch(tmp_path, ASTERISK_PROBE_IMAGE="fictional-image", ASTERISK_PROBE_DRIVER_SHA256="a" * 64)
    assert result.returncode == 0


def test_ladder_launch_rejects_missing_credentials_or_unknown_profile(tmp_path):
    for name in ("NEBIUS_API_KEY", "NEBIUS_PROJECT_ID", "ASTERISK_ALLOWED_HOSTS",
                 "ASTERISK_PREVIEW_PASSWORD", "ASTERISK_DB"):
        result = launch(tmp_path, ASTERISK_HOSTED_WORKFLOW="ladder", **{name: ""})
        assert result.returncode != 0 and name in result.stderr
    result = launch(tmp_path, ASTERISK_HOSTED_WORKFLOW="typo")
    assert result.returncode != 0 and "must be legacy or ladder" in result.stderr
