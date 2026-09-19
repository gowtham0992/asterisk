"""Portable verifier source. Integrity checks are not signatures or attestations."""
VERIFIER = '''import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text())
for name, expected_hash in manifest["files"].items():
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit("Bundle file missing or outside evidence directory: " + name)
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise SystemExit("Bundle integrity check failed: " + name)

# Check file integrity before importing the bundled checker.
from audit import execute
files = {p.name: p.read_bytes().decode("utf-8") for p in (root / "inputs").iterdir() if p.is_file()}
result = execute(json.loads((root / "rule.json").read_text()), files)
expected = json.loads((root / "report.json").read_text())["result"]
if result != expected:
    raise SystemExit("Evidence differs from the recorded result")
print(json.dumps(result, indent=2))
print("Evidence reproduced exactly.")
'''
