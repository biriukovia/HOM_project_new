"""Additional structural check, NOT the course's official check_week4.py.
Checks declared classes, relation endpoints, existential rules and file targets.
Cannot validate scientific meaning or whether a human really accepted a task.
"""
import argparse, re, sys
from pathlib import Path
import yaml

def audit(root, minimum=10):
    errors=[]
    def fail(s): errors.append(s)
    try: ont=yaml.safe_load((root/'ontology.yaml').read_text(encoding='utf-8'))
    except Exception as e: return [f'ontology.yaml: {e}'],0
    classes=ont.get('classes',{}); props=ont.get('properties',{}); rules=ont.get('rules',[])
    if len(classes)<3: fail('Нужно минимум 3 класса.')
    if len(rules)<2: fail('Нужно минимум 2 правила.')
    for cls in classes:
        if not (root/'ontology'/f'{cls}.md').is_file(): fail(f'Нет заметки класса: {cls}')
    def isa(t,expected):
        if isinstance(expected,list): return any(isa(t,x) for x in expected)
        seen=set()
        while t and t not in seen:
            if t==expected:return True
            seen.add(t); cfg=classes.get(t,{})
            t=cfg.get('parent') if isinstance(cfg,dict) else None
        return False
    objects={}; paths={}; count=0
    for folder in ['notes','tasks']:
        for f in sorted((root/folder).glob('*.md')):
            if f.name=='README.md': continue
            text=f.read_text(encoding='utf-8-sig'); m=re.match(r'^---\s*\n(.*?)\n---\s*\n',text,re.S)
            if not m: fail(f'{f.relative_to(root)}: нет YAML type');continue
            try: meta=yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError as e: fail(f'{f.name}: YAML {e}'); continue
            typ=meta.get('type')
            if typ not in classes:fail(f'{f.name}: неизвестный type {typ}');continue
            if f.stem in objects:fail(f'Неоднозначное имя заметки: {f.stem}');continue
            links={}
            for prop,targets in re.findall(r'^\s*-\s+([^:\n]+):\s*(.+)$',text,re.M):
                links.setdefault(prop.strip(),[]).extend(x.split('|')[0].split('#')[0] for x in re.findall(r'\[\[([^\]]+)\]\]',targets))
            if typ not in links.get('тип',[]):fail(f'{f.name}: нет - тип: [[{typ}]]')
            if typ=='Задача':
                allowed=(ont.get('attributes',{}).get('status',{}) or {}).get('values',[])
                if meta.get('status') not in allowed:fail(f'{f.name}: неизвестный status')
                if meta.get('status') in ['выполнена','принята'] and not re.search(r'^## Итог\b',text,re.M):fail(f'{f.name}: нет раздела Итог')
            else: count+=typ!='Файл'
            objects[f.stem]={'type':typ,'links':links,'path':f,'text':text}
            paths[f.relative_to(root).with_suffix('').as_posix()]=f.stem
    if count<minimum:fail(f'Предметных объектов: {count}, нужно минимум {minimum}.')
    def target_type(target):
        key=paths.get(target,target)
        if key in objects:return objects[key]['type']
        path=(root/target).resolve()
        if root.resolve() not in path.parents:return None
        if path.is_file():return 'Файл'
        return None
    for key,obj in objects.items():
        valid_links=0
        for prop,targets in obj['links'].items():
            if prop=='тип':continue
            if prop not in props:fail(f'{key}: отношение отсутствует в схеме: {prop}');continue
            spec=props[prop]
            if not isa(obj['type'],spec.get('domain')):fail(f'{key}: неверный domain для {prop}')
            for target in targets:
                typ=target_type(target)
                if not typ:fail(f'{key}: не найден конец связи {target}')
                elif not isa(typ,spec.get('range')):fail(f'{key}: {prop} -> {target}: неверный range {typ}')
                else:valid_links+=1
        if not valid_links:fail(f'{key}: нет связей с объектами/файлами по онтологии')
        for rule in rules:
            check=rule.get('check',{})
            if check.get('kind')=='some' and isa(obj['type'],check.get('class')):
                targets=obj['links'].get(check.get('property'),[])
                if not any(isa(target_type(t),check.get('target')) for t in targets):
                    fail(f'{key}: не выполнено правило {rule.get("id")}: {check.get("property")}')
            elif check.get('kind') not in (None,'some'):
                fail(f'Неподдерживаемое локальной проверкой правило {rule.get("id")}; нужен официальный checker.')
    return errors,count

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',nargs='?',default='.');p.add_argument('--minimum',type=int,default=10);a=p.parse_args()
    errors,count=audit(Path(a.root),a.minimum)
    print('Дополнительная проверка структуры графа; НЕ официальный check_week4.py.')
    print('Предметных объектов:',count)
    for e in errors:print('[НЕТ]',e)
    if not errors:print('[OK] Проверяемые локальные условия выполнены. Смысл и приёмка требуют проверки человеком.')
    return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
