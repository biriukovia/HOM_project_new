"""Reconcile recorded literature results without further network calls."""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from materialize_literature import write_note

archive = ROOT / "reports/literature2_codex_review"
archive.mkdir(exist_ok=True)
bad = ROOT / "notes/ЗапросКГрафу.md"
if bad.exists():
    shutil.move(str(bad), str(archive / "ЗапросКГрафу.goose-original.md"))

purpose = {
    "W2761960239": "Сравнительный пример интерференции HOM на плазмонной платформе. "
    "Он показывает другую физическую реализацию; не является работой о джиттере квантовой точки "
    "и не обосновывает параметры или форму exp*gauss.",
    "W2015275764": "Обзор многофотонной интерферометрии как общий контекст использования "
    "двухфотонной интерференции. Не является отдельной проверкой нашего ядра свёртки или T1.",
}
old = ("Работа отобрана по тематике неразличимости фотонов, джиттера или дефазирования "
       "в квантовых точках. Используется для обсуждения предпосылок модели; "
       "метаданные и аннотация не подтверждают форму нашего фита или извлечённое T1.")
for wid, explanation in purpose.items():
    p = ROOT / "notes" / (wid + ".md")
    shutil.copy2(p, archive / p.name)
    p.write_text(p.read_text(encoding="utf-8").replace(old, explanation), encoding="utf-8")

session = ROOT / "logs/literature2-20261020-185054-c7617"
records = [json.loads(s) for s in (session / "research_calls.jsonl").read_text(encoding="utf-8").splitlines()]
parts = []
for i, r in enumerate(records, 1):
    if r["tool"].startswith("wikidata"):
        parts.append(f"### Запись {i}: {r['tool']}\n```json\n" +
                     json.dumps({"arguments": r["kwargs"], "response": r.get("response")},
                                ensure_ascii=False, indent=2) + "\n```\n")
write_note("Wikidata_первый_опыт", {"type": "ЗапросКГрафу", "source": "Wikidata",
                                  "retrieved": "2026-10-20"},
           "Реальные пустые/отрицательные результаты сохранены ниже.\n\n"
           "Основная точка SPARQL не содержит научных статей (это указано в описании "
           "инструмента). ASK=false для Q51575871 не доказывает, что статья не относится "
           "к указанному классу; вывод Goose исправлен. Поиск сущности и SPARQL обращаются "
           "к разным наборам данных. Это не завершённое получение свойства понятия HOM.\n\n"
           f"Происхождение: `{session.relative_to(ROOT).as_posix()}/research_calls.jsonl`.\n\n"
           + "\n".join(parts), [("решает", "literature_search_2")])

for p in (ROOT / "notes").glob("Query_literature2*.md"):
    text = p.read_text(encoding="utf-8").replace(
        "Критерий: работы по джиттеру/дефазированию и неразличимости; последующая проверка openalex_work.",
        "Критерий: общий обзор многофотонной интерферометрии и сравнительная реализация HOM; "
        "последующая проверка openalex_work. Эти две работы не отобраны как источники по джиттеру квантовой точки.")
    p.write_text(text, encoding="utf-8")
print("Recorded literature notes reconciled; no new external requests.")
