"""Install the course's missing dependencies without inherited extra indexes."""
import os
import pathlib
import subprocess
import sys
import datetime

root = pathlib.Path(__file__).resolve().parents[2]
env = os.environ.copy()
for k in list(env):
    if k.startswith("PIP_"):
        del env[k]
# pip compares this value to os.devnull, case-sensitively.
env["PIP_CONFIG_FILE"] = os.devnull
cmd = [sys.executable, "-m", "pip", "install", "--index-url",
       "https://pypi.org/simple", "mcp>=1.0,<2.0",
       "sentence-transformers", "umap-learn", "matplotlib"]
dest = root / ("reports/week5_dependencies_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
with dest.open("w", encoding="utf-8") as f:
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    for line in p.stdout:
        f.write(line)
        f.flush()
        print(line, end="", flush=True)
    code = p.wait()
    f.write(f"\nEXIT_CODE={code}\n")
sys.exit(code)
