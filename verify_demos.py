# SPDX-License-Identifier: GPL-3.0-only
"""Exercise offline CLI contracts with public synthetic fixtures only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

def invoke(args, expected=0):
    process = subprocess.run([sys.executable, str(ROOT / "app.py"), *args], cwd=ROOT,
                             capture_output=True, text=True, timeout=15)
    assert process.returncode == expected, (process.returncode, process.stderr)
    if expected == 2:
        assert not process.stdout
        return None
    return json.loads(process.stdout)

report = invoke(["evaluate", "--input", "examples/demo.json"])
assert report["passed"] == 2 and report["evaluated"] == 3
assert invoke(["evaluate", "--input", "examples/demo.json", "--check"], 1) == report
probe = invoke(["plan", "--input", "examples/tasks.json"])
assert len(probe["probes"]) == 1
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "pending.json"
    path.write_text(json.dumps(probe["evaluation_template"]), encoding="utf-8")
    invoke(["evaluate", "--input", str(path)], 2)
    data = {"cases":[{"id":"a","relation":"equal","before":1,"after":1,"observed":True}]}
    path.write_text(json.dumps(data), encoding="utf-8")
    assert invoke(["evaluate", "--input", str(path), "--check"])["passed"] == 1
invoke(["plan", "--input", "examples/tasks.json", "--check"], 2)
print("6 offline CLI contracts passed; synthetic output relations only")
