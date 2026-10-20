"""Create fresh sibling workspaces for weeks 2–4. Never delete or overwrite a run."""
import datetime, json, pathlib, shutil, subprocess, sys
KIT = pathlib.Path(__file__).resolve().parent

def main():
    root = KIT.parent
    if not (root/'src/quick_fit.py').is_file():
        raise SystemExit('Put ollama_kit inside HOM_project_new before running this script.')
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    base = root.parent / ('HOM_course_runs_' + stamp)
    base.mkdir(exist_ok=False)
    paths = {}
    for name in ['w2-without','w2-with']:
        dest = base/name
        shutil.copytree(KIT/'examples/spectra_peaks', dest)
        contract = dest/'AGENTS.md'
        # Windows adaptation: do not claim that chmod was used on Windows.
        text = contract.read_text(encoding='utf-8')
        text = text.replace('`[среда]` — `chmod -R a-w data`',
                            '`[вызов]` — режим approve: оператор отклоняет команды изменения data/')
        if name == 'w2-without': contract.unlink()
        else: contract.write_text(text, encoding='utf-8')
        paths[name] = str(dest)
    for name in ['context-with','context-without']:
        dest = base/name
        shutil.copytree(root, dest, ignore=shutil.ignore_patterns(
            '.git', '.venv*', '__pycache__', 'ollama_kit', 'logs', '*.zip', '.env', '.env.*'))
        if name == 'context-without':
            p = dest/'AGENTS.md'; text = p.read_text(encoding='utf-8')
            # Exact two-line statement in the prepared project. Fail rather than editing an unknown contract.
            needle = '- схема однопроходная: изменение пути равно смещению, множителя 2 нет\n  (`diary.md`, уточнение 13.10); в коде сохранена поправка показателя группы воздуха;\n'
            if needle not in text:
                raise RuntimeError('The single-pass paragraph has changed. Remove only that paragraph manually in '+str(p))
            p.write_text(text.replace(needle, '', 1), encoding='utf-8')
        paths[name] = str(dest)
    dest = base/'demo-graph'
    shutil.copytree(KIT/'examples/demo_graph', dest)
    paths['demo-graph'] = str(dest)
    for name, path in paths.items():
        p = pathlib.Path(path)
        (p/'.gitignore').open('a', encoding='utf-8').write('\n__pycache__/\n.venv*/\n.env\n.env.*\n')
        for args in [['init','-q'], ['add','-A'], ['commit','-qm','Исходное состояние учебного опыта']]:
            result = subprocess.run(['git','-C',str(p),*args])
            if result.returncode:
                raise RuntimeError(f'Git failed for {p}; check git user.name/user.email. Files remain; do not rerun blindly.')
    (KIT/'workspace_paths.json').write_text(json.dumps(paths, ensure_ascii=False, indent=2), encoding='utf-8')
    (base/'paths.json').write_text(json.dumps(paths, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    print('Fresh copies prepared. Use the SAME model for both arms of each comparison.')
    print('Input protection: approve + operator review; no filesystem isolation is claimed.')
if __name__ == '__main__': main()
