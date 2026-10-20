"""Execute the prepared search notebook, retaining outputs and failures."""
import datetime
import json
import os
from pathlib import Path
import shutil
import sys

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"ollama_kit"))
from run_goose import find_agent, load_research_key

def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ROOT/"logs"/f"week5-notebook-{stamp}"
    out.mkdir()
    path = ROOT/"ollama_kit/week5/search_lab_hom.ipynb"
    shutil.copy2(path, out/"before.ipynb")
    env = os.environ.copy()
    agent, _ = find_agent()
    load_research_key(agent, env)
    env["PATH"] = str(Path(sys.executable).parent)+os.pathsep+env.get("PATH","")
    env["PYTHONUTF8"] = "1"
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=900, allow_errors=True,
                            resources={"metadata":{"path":str(ROOT)}})
    events=[]
    def save():
        serialized=nbformat.writes(nb)
        for key in ("OPENALEX_API_KEY","OPEN_ALEX"):
            if env.get(key): serialized=serialized.replace(env[key],"[REDACTED]")
        path.write_text(serialized,encoding="utf-8")
        (out/"execution.json").write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding="utf-8")
    try:
        with client.setup_kernel(env=env):
            for i,cell in enumerate(nb.cells):
                if cell.cell_type!="code": continue
                print(f"CELL {i} START",flush=True)
                client.execute_cell(cell,i)
                errors=[o.get("ename") for o in cell.get("outputs",[]) if o.output_type=="error"]
                events.append({"cell":i,"execution_count":cell.execution_count,"errors":errors,
                               "finished":datetime.datetime.now().astimezone().isoformat()})
                save()
                print(f"CELL {i} DONE errors={errors}",flush=True)
                if errors and i in (2,4,20):
                    print("Stopped: an essential setup cell failed.",flush=True)
                    break
    finally:
        save()
    failed=any(e["errors"] for e in events)
    print("Network exceptions printed by cells still require review; no errors is not proof of network success.")
    return int(failed)

if __name__=="__main__":
    raise SystemExit(main())
