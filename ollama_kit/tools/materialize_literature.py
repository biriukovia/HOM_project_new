"""Format real recorded MCP replies as graph notes; never invent API responses."""
from pathlib import Path
import datetime
import json
import shutil
import sys
import yaml

ROOT=Path(__file__).resolve().parents[2]

def write_note(name, meta, body, links):
    p=ROOT/"notes"/f"{name}.md"
    p.write_text("---\n"+yaml.safe_dump(meta,allow_unicode=True,sort_keys=False)+"---\n"
                 f"# {name}\n\n{body}\n\n## Связи\n- тип: [[{meta['type']}]]\n"+
                 "".join(f"- {k}: [[{v}]]\n" for k,v in links),encoding="utf-8")

def main():
    session=ROOT/"logs"/sys.argv[1]
    records=[json.loads(s) for s in (session/"research_calls.jsonl").read_text(encoding="utf-8").splitlines()]
    works={}
    for i,r in enumerate(records):
        w=r.get("response",{}).get("work")
        if w and w.get("openalex_id"):
            works[w["openalex_id"]]=(i,r,w)
    if not works:
        raise SystemExit("No real openalex_work responses: nothing written")
    stamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    before=ROOT/"reports"/f"literature_formatting_{stamp}"
    before.mkdir()
    for p in (ROOT/"notes").glob("*.md"):
        if p.stem in works or p.stem.startswith(("Query_","Автор_","Запрос_")):
            shutil.copy2(p,before/p.name)
    taskname="literature_search" if len(works)==3 else "literature_search_2"
    # Existing first-pass task criteria are preserved verbatim in the session snapshot.
    task=ROOT/"tasks"/f"{taskname}.md"
    if task.exists():shutil.copy2(task,before/task.name)
    queries=[]
    for wid,(i,r,w) in works.items():
        provenance=r["response"]["provenance"]
        query=f"Запрос_{session.name}_{i+1}"
        queries.append(query)
        write_note(query,{"type":"ЗапросКГрафу","source":provenance.get("source"),
                         "retrieved":provenance.get("retrieved")},
                   f"Инструмент: `{r['tool']}`.\n\nАргументы:\n```json\n"+
                   json.dumps(r["kwargs"],ensure_ascii=False,indent=2)+
                   f"\n```\n\n[источник] Получена одна запись, выбрана одна: {wid}.\n"
                   f"Адрес: {provenance.get('request')}.\n"
                   f"Полный ответ: `{session.relative_to(ROOT).as_posix()}/research_calls.jsonl`, запись {i+1}.\n"
                   "Форматирование Codex по сохранённому реальному ответу Goose MCP.",
                   [("решает",taskname)])
        authorlinks=[]
        for a in w.get("authors",[])[:3]:
            aid=a.get("openalex_id")
            if not aid:continue
            name=f"Автор_{aid}"
            write_note(name,{"type":"Автор","openalex_id":aid},
                       f"[источник] {a['name']}. Идентификатор и имя из ответа OpenAlex для {wid}.\n"
                       f"Происхождение: `{session.relative_to(ROOT).as_posix()}/research_calls.jsonl`, запись {i+1}.\n"
                       "Связан входящим отношением написан от источника. Исходящих отношений этого класса в схеме нет.",[])
            authorlinks.append(("написан",name))
        meta={"type":"Источник","openalex_id":wid}
        for field in ("doi","year","oa_status"):
            if w.get(field) is not None:meta[field]=w[field]
        meta["cited_by"]=w.get("cited_by")
        authors=", ".join(a["name"] for a in w.get("authors",[]))
        body=(f"[источник] {authors}. **{w['title']}**. {w.get('source','')}, {w.get('year','')}. "
              f"Том {w.get('volume','не указан')}, выпуск {w.get('issue','не указан')}, "
              f"страницы/номер статьи {w.get('pages','не указаны')}. DOI: {w.get('doi','не указан')}.\n\n"
              "[порождено] Работа отобрана по тематике неразличимости фотонов, джиттера или дефазирования "
              "в квантовых точках. Используется для обсуждения предпосылок модели; "
              "метаданные и аннотация не подтверждают форму нашего фита или извлечённое T1.\n\n"
              "Расхождение: личная сверка с издателем не выполнена.\n"
              "Полный текст не скачивался; принятие пользователем не получено.")
        write_note(wid,meta,body,[("найденЗапросом",query),*authorlinks])
    # Repair the malformed search note from the first Goose pass using its actual query.
    searches=[(i,r) for i,r in enumerate(records) if r["tool"]=="openalex_search" and "results" in r.get("response",{})]
    for i,r in searches:
        response=r["response"];prov=response["provenance"]
        name="Query_OpenAlex_20261020" if taskname=="literature_search" else f"Query_{session.name}_{i+1}"
        returned={w["openalex_id"] for w in response["results"]}
        chosen=sorted(set(works)&returned)
        write_note(name,{"type":"ЗапросКГрафу","source":"OpenAlex","retrieved":prov.get("retrieved")},
                   "Инструмент: `openalex_search`.\n\nАргументы:\n```json\n"+
                   json.dumps(r["kwargs"],ensure_ascii=False,indent=2)+
                   f"\n```\n\nНайдено сервисом: {response.get('found')}; возвращено: {len(response['results'])}; "
                   f"отобрано из этой выдачи: {len(chosen)} ({', '.join(chosen)}).\n"
                   f"Критерий: работы по джиттеру/дефазированию и неразличимости; последующая проверка openalex_work.\n"
                   f"Полный ответ: `{session.relative_to(ROOT).as_posix()}/research_calls.jsonl`, запись {i+1}.",
                   [("решает",taskname)])
    model=ROOT/"notes/Модель_exp_gauss.md"
    text=model.read_text(encoding="utf-8")
    for wid in works:
        link=f"- основанаНа: [[{wid}]]"
        if link not in text:text+="\n"+link+"\n"
    if "Связи с литературой" not in text:
        text+="\nСвязи с литературой относятся к обсуждению механизмов джиттера и дефазирования. "
        text+="Они не утверждают, что каждая статья выводит именно эту формулу или подтверждает наши параметры.\n"
    model.write_text(text,encoding="utf-8")
    task.write_text(f"---\ntype: Задача\nstatus: выполнена\n---\n# {taskname}\n\n"
                   f"## Запрос пользователя\nСобрать {'три' if len(works)==3 else 'ещё две'} реальные неповторяющиеся работы по теме HOM.\n\n"
                   "## Готово, когда\nИсточники зафиксированы в notes/, созданы соответствующие заметки авторов "
                   "и запросов, установлены связи по онтологии, выполнен аудит графа.\n\n"
                   "## Не входит\nСбор PDF, личная сверка и приёмка за пользователя.\n\n"
                   "## Итог\nРеальные запросы выполнены Goose/Ollama gemma4:31b-cloud. "
                   "Заметки оформлены Codex по сохранённым ответам после остановки сессии. "
                   "Аудит и его ограничения фиксируются в отчёте; ожидает личной проверки.\n\n"
                   "## Связи\n- тип: [[Задача]]\n- результатЗадачи: [[Отчёт_литературного_сбора]]\n",
                   encoding="utf-8")
    report=ROOT/"reports/literature_collection.md"
    sources=[]
    for p in (ROOT/"notes").glob("W*.md"):
        if "type: Источник" in p.read_text(encoding="utf-8"):sources.append(p.stem)
    report.write_text("# Литературный сбор\n\nРеальные ответы MCP находятся в logs/literature*/research_calls.jsonl.\n"
                      "Goose выполнял поиск; Codex оформил заметки из записанных ответов. "
                      "Это не автономный успешный проход оформления графа Goose.\n\n"
                      "Источники: "+", ".join(sources)+".\n\n"
                      "У Автор и Ограничение схема не задаёт исходящих отношений; локальный аудитор "
                      "ошибочно требует их у каждого узла. Его код не обнулялся изменением проверки.\n"
                      "Личная сверка DOI и приёмка ещё не получены.\n",encoding="utf-8")
    write_note("Отчёт_литературного_сбора",{"type":"Отчёт"},
               "Сводка реального сбора и ограничения проверки.",
               [("хранитсяВ","reports/literature_collection.md"),("описывает","Независимая_проверка")])
    print("Formatted real works:",", ".join(works))

if __name__=="__main__":main()
