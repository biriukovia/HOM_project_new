"""Inventory of evidence. This is not an automatic grade or an official course checker."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_graph import audit

def main():
    pending=[]
    def check(label,ok):
        print(('[OK] ' if ok else '[НУЖНО] ')+label)
        if not ok:pending.append(label)
    check('Файл нового HOM-фита', (ROOT/'results/course_fit.json').is_file())
    print('Числа проверяются отдельно: python checks/check.py')
    runs=[]
    for f in (ROOT/'logs').glob('*/run.json'):
        try:r=json.loads(f.read_text(encoding='utf-8'));r['_dir']=f.parent;runs.append(r)
        except (ValueError,OSError):pass
    for task in ['fit','paper','index','graph1','graph2','mcp-test','literature1','literature2']:
        candidates=[r for r in runs if r.get('task')==task]
        check('Сохранён реальный экспорт Goose: '+task, any((r['_dir']/'session.json').is_file() or (r['_dir']/'session.md').is_file() for r in candidates))
    print('Существование экспорта не доказывает успех: прочитайте ошибки, вызовы и личный итог.')
    check('Ноутбук недели 3: журнал и результат критерия',any((d/'journal.csv').is_file() and (d/'result.json').is_file() for d in (ROOT/'logs').glob('week3-notebook-*')))
    for d in (ROOT/'logs').glob('week3-notebook-*'):
        f=d/'result.json'
        if f.exists():print('  Критерий в',d.name,':',json.loads(f.read_text(encoding='utf-8')).get('criterion_passed'))
    text=(ROOT/'memory/L2.md').read_text(encoding='utf-8') if (ROOT/'memory/L2.md').is_file() else ''
    rows=[line for line in text.splitlines() if re.match(r'^\|\s*\d+\s*\|',line)]
    check('Не менее трёх заполненных строк сверки L2 (содержимое проверить по PDF)',sum(not re.search(r'заполнить|не проверено|…|\.\.\.',row,re.I) for row in rows)>=3)
    errors,count=audit(ROOT)
    check('Локальная структурная проверка графа',not errors)
    for err in errors[:6]:print(' ',err)
    lib=ROOT/'library_search/my_library.json'
    docs=json.loads(lib.read_text(encoding='utf-8')).get('documents',[]) if lib.exists() else []
    check('Личная библиотека: >=20 разных документов',len({d.get('id') for d in docs if d.get('id')})>=20)
    f=ROOT/'reports/my_search_report.md';report=f.read_text(encoding='utf-8') if f.exists() else ''
    comments=[s for s in report.splitlines() if s.startswith('[написано]')]
    check('Пять запросов в отчёте',len(re.findall(r'^## ',report,re.M))>=5)
    check('Пять заполненных комментариев (авторство подтверждает человек)',sum(len(s)>25 and '…' not in s and 'Что подошло и чем выдачи отличаются:' not in s for s in comments)>=5)
    sources=[];sparql=False
    for f in (ROOT/'notes').glob('*.md'):
        t=f.read_text(encoding='utf-8')
        if re.search(r'^type:\s*Источник\s*$',t,re.M) and 'openalex_id' in t and 'найденЗапросом' in t:sources.append(f)
        if re.search(r'^type:\s*ЗапросКГрафу\s*$',t,re.M) and re.search(r'\b(SELECT|ASK)\b',t):sparql=True
    check('>=5 источников с идентификаторами и происхождением',len(sources)>=5)
    check('Сохранён текст SPARQL в заметке запроса',sparql)
    check('Сохранены реальные ответы research MCP',any((r['_dir']/'research_calls.jsonl').is_file() for r in runs))
    for name in ['check_week3.py','check_week4.py']:
        check('Официальный скрипт курса: '+name,(ROOT/name).is_file())
    print('\nВручную: сравнения недель 2 и 3 (в отдельных копиях), три DOI, личная приёмка,')
    print('граф в Obsidian, git-коммиты и доступная преподавателю ссылка. См. HUMAN_CHECKLIST.md.')
    print('Незаполненных автоматических пунктов:',len(pending))
    return int(bool(pending))
if __name__=='__main__':raise SystemExit(main())
