"""Read-only delivery checks; outputs never contain secret values."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout

secrets = set()
envfile = Path.home() / "AI4Science/.env"
if envfile.exists():
    for line in envfile.read_text(encoding="utf-8-sig").splitlines():
        key, sep, value = line.partition("=")
        if sep and any(s in key.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            value = value.strip().strip("'\"")
            if len(value) >= 12:
                secrets.add(value.encode())
patterns = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{25,}"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}"),
]
def sensitive(data):
    return any(s in data for s in secrets) or any(p.search(data) for p in patterns)

files = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")
findings = []
total = 0
largest = []
for raw in files:
    if not raw:
        continue
    name = raw.decode("utf-8")
    p = ROOT / name
    if not p.is_file():
        continue
    data = p.read_bytes()
    total += len(data)
    largest.append((len(data), name))
    if sensitive(data):
        findings.append({"location": "working_tree", "path": name})
objects = git("rev-list", "--objects", "--all").splitlines()
history_blobs = 0
for obj in objects:
    sha, _, name = obj.partition(b" ")
    if git("cat-file", "-t", sha.decode()).strip() != b"blob":
        continue
    history_blobs += 1
    if sensitive(git("cat-file", "blob", sha.decode())):
        findings.append({"location": "history", "object": sha.decode(),
                         "path": name.decode("utf-8", errors="replace")})

protected = {}
for folder in ("data", "checks"):
    for p in (ROOT / folder).rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            protected[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
violations = []
for run in (ROOT / "logs").glob("*/run.json"):
    d = json.loads(run.read_text(encoding="utf-8"))
    # Preserve differing metadata formats; compare any available before/after hashes.
    for key, value in d.items():
        if key.startswith("protected") and isinstance(value, dict):
            for name, h in value.items():
                if name in protected and isinstance(h, str) and len(h) == 64 and h != protected[name]:
                    violations.append({"run": str(run.relative_to(ROOT)), "field": key, "path": name})

report = {
    "date": "2026-10-20",
    "secret_scan": {"known_secret_values_loaded": len(secrets),
                    "patterns": "private key headers, GitHub tokens, sk-style API tokens",
                    "findings": findings, "history_blobs_examined": history_blobs,
                    "limitation": "Only listed token patterns and configured known secrets; not a universal proof."},
    "working_tree_file_count": len([f for f in files if f]),
    "total_bytes": total,
    "largest_files": sorted(largest, reverse=True)[:12],
    "protected_hashes": protected,
    "protected_hash_mismatches": violations,
    "protected_git_changes": git("diff", "--name-only", "748154e", "--", "data", "checks", "results",
                                  "paper", "ontology.yaml").decode("utf-8"),
}
(ROOT / "reports/delivery_integrity.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"files": report["working_tree_file_count"], "secret_findings": len(findings),
                  "protected_hash_mismatches": len(violations),
                  "history_blobs": history_blobs, "total_MB": round(total / 1e6, 1)}, ensure_ascii=False))
raise SystemExit(bool(findings or violations))
