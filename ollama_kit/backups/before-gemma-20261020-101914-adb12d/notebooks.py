"""Launch the week 3 or 5 notebook in the current project Python environment."""
import argparse, os, pathlib, subprocess, sys
from run_goose import find_agent, load_research_key
p=argparse.ArgumentParser();p.add_argument('week',choices=['3','5']);p.add_argument('--model',default='deepseek-v4.1-flash:cloud');p.add_argument('--agent-dir');a=p.parse_args()
kit=pathlib.Path(__file__).resolve().parent
env=os.environ.copy();env['HOM_NOTEBOOK_MODEL']=a.model;env['PYTHONUTF8']='1'
try:
 agent,_=find_agent(a.agent_dir);load_research_key(agent,env)
except RuntimeError: pass
name='week3/agent_loop_ollama.ipynb' if a.week=='3' else 'week5/search_lab_hom.ipynb'
raise SystemExit(subprocess.call([sys.executable,'-m','jupyterlab',str(kit/name),'--ServerApp.root_dir='+str(kit.parent)],env=env,cwd=kit.parent))
