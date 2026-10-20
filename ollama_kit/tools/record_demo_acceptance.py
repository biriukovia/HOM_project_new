"""Record the user's explicit acceptance in the separate demo repository."""
from pathlib import Path
import json
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[2]
demo = Path(json.loads((ROOT / "ollama_kit/workspace_paths.json").read_text(encoding="utf-8"))["demo-graph"])
task = demo / "tasks/Подготовить отчет по закону Аррениуса.md"
text = task.read_text(encoding="utf-8")
text = text.replace("status: выполнена", "status: принята")
text += "\n## Решение пользователя\n20.10.2026: «Принимаю оба отчёта» (HOM и Аррениус).\n"
task.write_text(text, encoding="utf-8")
report = demo / "reports/arrhenius_report.md"
text = report.read_text(encoding="utf-8")
text += "\nПриёмка пользователя 20.10.2026: «Принимаю оба отчёта» (HOM и Аррениус).\n"
report.write_text(text, encoding="utf-8")
with (demo / "diary.md").open("a", encoding="utf-8") as f:
    f.write("\n## 2026-10-20 — личная приёмка отчёта\n"
            "Пользователь: «Принимаю оба отчёта» (HOM и Аррениус). "
            "Codex записал решение после завершения второй сессии; численные данные не менялись.\n")
subprocess.run(["git", "-C", str(demo), "add", "diary.md", str(task), str(report)], check=True)
subprocess.run(["git", "-C", str(demo), "commit", "-m", "Личная приёмка отчёта Аррениуса"], check=True)
dest = ROOT / "reports/experiments-20261020-190728/demo-graph"
for rel in ("diary.md", "tasks/Подготовить отчет по закону Аррениуса.md", "reports/arrhenius_report.md"):
    shutil.copy2(demo / rel, dest / rel)
for label, args in (("status", ["status", "--short"]), ("history", ["log", "--oneline"]),
                    ("last_commit", ["show", "--format=fuller", "--stat", "HEAD"])):
    r = subprocess.run(["git", "-C", str(demo), *args], capture_output=True, text=True, encoding="utf-8", check=True)
    (dest / (label + ".txt")).write_text(r.stdout, encoding="utf-8")
subprocess.run(["git", "-C", str(demo), "bundle", "create", str(dest / "history.bundle"), "--all"], check=True)
print("Demo acceptance recorded; delivery snapshot and Git bundle updated.")
