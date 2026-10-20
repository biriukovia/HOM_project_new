"""Copy actual experiment logs and Git diffs into the main project; never copy nested .git."""
import datetime,json,pathlib,shutil,subprocess
KIT=pathlib.Path(__file__).resolve().parent
ROOT=KIT.parent
paths=json.loads((KIT/'workspace_paths.json').read_text(encoding='utf-8'))
out=ROOT/'reports'/('experiments-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
out.mkdir(parents=True,exist_ok=False)
for name,path in paths.items():
 src=pathlib.Path(path);dest=out/name;dest.mkdir()
 if (src/'logs').is_dir():shutil.copytree(src/'logs',dest/'logs')
 if (src/'AGENTS.md').is_file():shutil.copy2(src/'AGENTS.md',dest/'AGENTS_used.md')
 for label,args in [('status',['status','--short']),('history',['log','--oneline']),('changes',['diff','HEAD','--','.',':(exclude)logs']),('last_commit',['show','--format=fuller','--stat','HEAD'])]:
  r=subprocess.run(['git','-C',str(src),*args],capture_output=True,text=True,encoding='utf-8',errors='replace')
  (dest/(label+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
 # Save current generated artifacts for the supplied demo projects only.
 if name in ('w2-with','w2-without','demo-graph'):
  for folder in ('src','results','reports','notes','tasks','ontology','data','checks','library','.obsidian'):
   if (src/folder).is_dir():shutil.copytree(src/folder,dest/folder,ignore=shutil.ignore_patterns('__pycache__','.env','.env.*'))
  if (src/'diary.md').is_file():shutil.copy2(src/'diary.md',dest/'diary.md')
  if (src/'ontology.yaml').is_file():shutil.copy2(src/'ontology.yaml',dest/'ontology.yaml')
  if name=='demo-graph':
   r=subprocess.run(['git','-C',str(src),'bundle','create',str(dest/'history.bundle'),'--all'],capture_output=True,text=True,encoding='utf-8',errors='replace')
   if r.returncode:raise RuntimeError('Could not preserve demo Git history: '+r.stderr)
print(out)
print('Copied actual available evidence only; missing runs remain missing. Review before git add.')
