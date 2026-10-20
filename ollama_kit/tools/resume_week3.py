"""Resume only the missing model comparison and interrupted protection experiment."""
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[2]
path=ROOT/"ollama_kit/week3/agent_loop_ollama.ipynb"
stamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
out=ROOT/"logs"/f"week3-resume-{stamp}"
out.mkdir()
shutil.copy2(path,out/"before.ipynb")
nb=nbformat.read(path,as_version=4)

def src(i):return nb.cells[i].source
init=[src(3),src(5).split("\nreply = ask(")[0],
      src(7).split("\nreply = ask(")[0],src(10),
      src(11).split("\nenv = new_env()")[0],src(14),
      src(16).split("# MODELS заданы")[0],
      src(20).split("\nenv = new_env()")[0],src(22),
      src(32).split("\nenv = env_injected()")[0]]
comparison=src(16)
comparison=comparison.replace("# policy =","policy =").replace("#                                 .value_counts()", "                                 .value_counts()")
comparison=comparison.replace("#           for m in MODELS}","           for m in MODELS}")
comparison=comparison.replace("# pd.DataFrame(policy)","pd.DataFrame(policy)")
work=nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(s) for s in init]+[
    nbformat.v4.new_code_cell(comparison),nbformat.v4.new_code_cell(src(34))])
env=os.environ.copy()
env["PATH"]=str(Path(sys.executable).parent)+os.pathsep+env.get("PATH","")
env["PYTHONUTF8"]="1"
client=NotebookClient(work,timeout=5400,allow_errors=False,
                      resources={"metadata":{"path":str(ROOT)}})
events=[]
try:
    with client.setup_kernel(env=env):
        for i,cell in enumerate(work.cells):
            print("CELL",i,"START",flush=True)
            try:
                client.execute_cell(cell,i)
            finally:
                nbformat.write(work,out/"executed.ipynb")
                if i>=len(init):
                    target=16 if i==len(init) else 34
                    nb.cells[target].source=cell.source
                    nb.cells[target].outputs=cell.outputs
                    nb.cells[target].execution_count=cell.execution_count
                    nb.cells[target].metadata["resumed_from"]=out.relative_to(ROOT).as_posix()
                    nbformat.write(nb,path)
            events.append({"cell":i,"target":16 if i==len(init) else 34 if i==len(init)+1 else None,
                           "finished":datetime.datetime.now().astimezone().isoformat()})
            (out/"execution.json").write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding="utf-8")
            print("CELL",i,"DONE",flush=True)
finally:
    nbformat.write(work,out/"executed.ipynb")
