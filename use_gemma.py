"""Switch the prepared HOM Ollama kit to Gemma without replacing experiment logs.

Run from the HOM project root: python use_gemma.py
Only the two launchers and the unexecuted week-3 notebook are changed.
Original bytes are backed up before any write. No network or model calls.
"""
from pathlib import Path
import datetime
import json
import shutil
import sys
import uuid

OLD = "deepseek-v4.1-flash:cloud"
NEW = "gemma4:31b-cloud"


def main():
    root = Path.cwd()
    kit = root / "ollama_kit"
    if not (root / "src" / "quick_fit.py").is_file():
        raise SystemExit("Run this script from the HOM_project_new project root.")
    paths = [kit / "run_goose.py", kit / "notebooks.py",
             kit / "week3" / "agent_loop_ollama.ipynb"]
    changes = []
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"Missing file: {path}. No files have been changed.")
        original = path.read_bytes()
        source = original.decode("utf-8-sig")
        if path.suffix == ".ipynb":
            notebook = json.loads(source)
            needs_change = any(OLD in "".join(c.get("source", []))
                               for c in notebook["cells"])
            if needs_change and any(c.get("outputs") or c.get("execution_count") is not None
                                    for c in notebook["cells"] if c["cell_type"] == "code"):
                raise SystemExit("The week-3 notebook already contains execution evidence. "
                                 "No files have been changed. Keep it and ask for a separate fresh notebook.")
            if needs_change:
                for cell in notebook["cells"]:
                    text = "".join(cell.get("source", []))
                    text = text.replace(OLD, NEW).replace("DeepSeek V4.1 Flash cloud", "Gemma 4 31B cloud")
                    cell["source"] = text.splitlines(keepends=True)
                source = json.dumps(notebook, ensure_ascii=False, indent=1) + "\n"
        else:
            needs_change = OLD in source
            source = source.replace(OLD, NEW)
            compile(source, str(path), "exec")
        if needs_change:
            changes.append((path, original, source.encode("utf-8")))
    if not changes:
        print("No changes needed: no old DeepSeek model settings found.")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    backup = kit / "backups" / ("before-gemma-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    for path, original, _ in changes:
        dest = backup / path.relative_to(kit)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(original)
    written = []
    try:
        for path, original, replacement in changes:
            written.append((path, original))
            path.write_bytes(replacement)
    except OSError:
        for path, original in reversed(written):
            path.write_bytes(original)
        raise
    record = {
        "action": "Switch kit defaults and week-3 comparison from DeepSeek to Gemma",
        "from": OLD, "to": NEW,
        "changed": [str(p.relative_to(root)) for p, _, _ in changes],
        "backup": str(backup.relative_to(root)),
        "model_calls_performed": False,
        "note": "Past logs and results were not changed. Local comparison models remain qwen3:8b and qwen3:4b.",
    }
    (backup / "change.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))
    print("READY. Start notebooks.py 3 --model gemma4:31b-cloud")


if __name__ == "__main__":
    main()
