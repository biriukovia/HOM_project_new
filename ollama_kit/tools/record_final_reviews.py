"""Record actual user replies from 20 October; no network or model calls."""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from materialize_literature import write_note

def read(name):
    return (ROOT / name).read_text(encoding="utf-8")
def write(name, text):
    (ROOT / name).write_text(text, encoding="utf-8")

backup = ROOT / "reports/final_review_before"
backup.mkdir(exist_ok=True)
for name in ("memory/L2.md", "notes/Запрос_WD_QuantumSuperposition.md", "tasks/wikidata_concept.md"):
    shutil.copy2(ROOT / name, backup / Path(name).name)

comments = [
    "Отличаются выдачи во второй позиции. Больше подходит вектор",
    "Отличаются 2ой и 3ей выдачей. Больше подходит выдача BM25",
    "BM25 не выдала ничего",
    "Различаются в одной позиции. Больше подходит BM25",
    "Различаются в двух выдачах. Больше подходит BM25",
]
text = read("reports/my_search_report.md")
placeholder = "[написано] Что подошло и чем выдачи отличаются: …"
if text.count(placeholder) != 5:
    raise SystemExit("Expected five original placeholders; do not rerun after personal edits.")
for c in comments:
    text = text.replace(placeholder, "[написано] " + c, 1)
text += ("\nКомментарии 1–5 переданы пользователем 20.10.2026 и перенесены Codex дословно.\n"
         "Это оценка релевантности пользователем, а не автоматическая метрика.\n")
write("reports/my_search_report.md", text)

text = read("memory/L2.md").split("## Сверка с оригиналом")[0]
text += """## Сверка с оригиналом — 20.10.2026

Пользователь лично сообщил для тезисов 10 (PDF с. 11), 4 (с. 4–5)
и 8 (с. 10): «верно определено». Дословные цитаты ниже перенёс Codex из PDF
и сверил с изображениями страниц 5, 10 и 11; переносы строк убраны, формулы
переданы в математической записи. Это разделение авторства относится и к итогам:
вердикты принадлежат пользователю, техническое заполнение таблицы — ассистенту.
Прежние несогласованные черновые строки сохранены в reports/final_review_before/L2.md.

|№|Тезис|Стр.|Цитата из оригинала|Итог|
|-|-|-|-|-|
|1|10: 88% и около 3 см|11|“The obtained value of indistinguishability, corrected using Eq. (B4), was 88% and the photon coherence length was about 3 cm.”|Пользователь: «верно определено». Черновая цитата о F=99.6% относилась к другому результату; она заменена.|
|2|4: улучшение при росте числа мод и шуме 10%|5 (в пределах указанных пользователем с. 4–5)|“We also simulated how the quality of reconstruction changes with the number of modes and, surprisingly, find that it improves (Fig. 3), while the results of SST [9] become worse. The noise level was fixed to be 10% of the absolute value of visibilities.”|Пользователь: «верно определено». В черновой строке было ошибочное «точность снижается»; тезис 4 уже содержал правильное направление.|
|3|8: пренебрежение когерентностью и многофотонной компонентой; малая ненулевая примесь в опыте|10|“If we neglect all effects related to photon coherence and the multiphoton component in the state ρ̂ (b₀ = c⁽¹⁾ = c⁽²⁾ = g⁽²⁾(0) = 0)” … “Additionally, the source itself has a low multiphoton component: the measured value, g⁽²⁾(0) ≈ 0.03.”|Пользователь: «верно определено». В черновой строке был текст о фазовой неоднозначности другого тезиса; он заменён.|

Цитаты подтверждают указанные части тезисов, а не автоматически все десять тезисов L2.
Числа статьи 88% и около 3 см не подставляются вместо параметров текущего HOM-фита.
"""
write("memory/L2.md", text)

session = "wikidata-concept-20261020-190352-accf2"
records = [json.loads(s) for s in read(f"logs/{session}/research_calls.jsonl").splitlines()]
idx, record = next((i, r) for i, r in enumerate(records, 1) if r["tool"] == "wikidata_sparql")
response = record["response"]
write_note("Запрос_WD_QuantumSuperposition",
           {"type": "ЗапросКГрафу", "source": "Wikidata Query Service", "retrieved": "2026-10-20"},
           "Понятие quantum superposition, Q830791, получено поиском Wikidata (предыдущая запись журнала).\n\n"
           "Точный запрос:\n```sparql\n" + record["kwargs"]["query"] +
           "\n```\n\nФактический ответ:\n```json\n" +
           json.dumps(response, ensure_ascii=False, indent=2) +
           f"\n```\n\nПроисхождение: `logs/{session}/research_calls.jsonl`, запись {idx}.\n"
           "Получено пять строк, для связи с проектом выбрано одно свойство: P227 = 4346012-4.\n"
           "Другие значения сохранены как идентификаторы без выдуманных подписей.\n"
           "В черновике Goose ошибочно подписал Q1293220 как quantum mechanics, не запрашивая метку. "
           "Эта подпись удалена; исходный черновик сохранён в reports/final_review_before/.\n"
           "Текстовая ссылка и значение добавлены в Модель_exp_gauss. Общее понятие "
           "суперпозиции не подтверждает форму или параметры нашего фита.\n"
           "Оформлено Codex после остановки Goose на двух ошибках редактирования.",
           [("решает", "wikidata_concept")])
text = read("notes/Модель_exp_gauss.md")
# These two background works are not foundations of the fitted kernel.
for wid in ("W2761960239", "W2015275764"):
    text = text.replace(f"- основанаНа: [[{wid}]]", "")
text += """\n## Общий литературный контекст и Wikidata

[[W2015275764]] — обзор многофотонной интерферометрии;
[[W2761960239]] — сравнительная реализация HOM на плазмонной платформе.
Это литературный фон; отношение основанаНа к ядру exp*gauss им не присвоено.
Обе записи связаны с запросами, авторами и задачей сбора.

Понятие quantum superposition: Q830791. Реальное свойство P227 = `4346012-4`.
Точный SELECT, пять полученных строк и происхождение:
[[Запрос_WD_QuantumSuperposition]]. Связь отражает общий принцип суперпозиции
в интерференции; она не является проверкой формы HOM-провала или его параметров.
"""
write("notes/Модель_exp_gauss.md", text)
text = read("tasks/wikidata_concept.md").replace("status: открыта", "status: выполнена")
text = text.replace("(заполняется по завершении)",
                    f"Goose выполнил поиск и SELECT; возвращено 5 строк, `logs/{session}/research_calls.jsonl`.\n"
                    "После двух ошибок редактирования сессия остановлена. Codex оформил "
                    "ответ без новых внешних запросов и добавил ссылку в модель.\n"
                    "Проверка графа: python ollama_kit/tools/audit_graph.py .; фактический "
                    "вывод и ограничения — reports/final_checks.json.\n")
text += "\n## Связи\n- тип: [[Задача]]\n- результатЗадачи: [[Отчёт_литературного_сбора]]\n"
write("tasks/wikidata_concept.md", text)

for name in ("tasks/literature_search.md", "tasks/literature_search_2.md"):
    text = read(name).replace("status: выполнена", "status: принята")
    text += "\n## Решение пользователя\n20.10.2026: «Принимаю литературный сбор».\n"
    write(name, text)
for p in (ROOT / "notes").glob("W*.md"):
    text = p.read_text(encoding="utf-8")
    if "type: Источник" in text:
        text = text.replace("принятие пользователем не получено", "сбор принят пользователем 20.10.2026")
        text += "\nПриёмка сбора: «Принимаю литературный сбор», 20.10.2026. Это не новая сверка отдельных DOI.\n"
        p.write_text(text, encoding="utf-8")

text = read("tasks/course_summary_report.md").replace("status: выполнена", "status: принята")
text += "\n## Решение пользователя\n20.10.2026: «Принимаю оба отчёта» (HOM и Аррениус).\n"
write("tasks/course_summary_report.md", text)
text = read("reports/course_summary.md").replace("Ожидает личной проверки.",
          "Принят пользователем 20.10.2026: «Принимаю оба отчёта» (HOM и Аррениус).")
write("reports/course_summary.md", text)

write("reports/literature_collection.md", """# Литературный сбор — принят 20.10.2026

Решение пользователя: «Принимаю литературный сбор».
Три DOI лично сверены: «Все данные верны. Проверил сегодня 20.10.2026».
Поля и дата — reports/personal_doi_review.md. Отсутствующие в OpenAlex номера
статей не выдумывались; подтверждение пользователя не создаёт недостающих полей.

| Работа | Роль |
|---|---|
| W2098850878 | Неразличимость фотонов квантовой точки, дефазирование и джиттер |
| W2203037887 | Условия возбуждения неразличимых фотонов |
| W2914019725 | Неразличимость при некогерентном возбуждении |
| W2015275764 | Общий обзор многофотонной интерферометрии |
| W2761960239 | Сравнительная реализация HOM на плазмонной платформе |

Первые три связаны с обсуждением механизмов модели exp*gauss.
Последние две — литературный фон, не обоснование нашего ядра свёртки или T1.
Все пять источников имеют авторов, запросы и фактические метаданные.
PDF не скачивались. Метаданные и приёмка не подтверждают истинность HOM-модели.

Реальные сессии:
- logs/mcp-test-20261020-184104-9c22e/ — проверочный ответ MCP.
- logs/literature1-20261020-184452-3c204/ — первые три работы; контекст исчерпан.
- logs/literature2-20261020-185054-c7617/ — две дополнительные работы и первый опыт Wikidata.
- logs/wikidata-concept-20261020-190352-accf2/ — успешный SELECT для понятия Q830791.

В research_calls.jsonl сохранены инструменты, аргументы, даты, ответы,
найденные и возвращённые количества; заметки запросов фиксируют отбор.
Goose выполнял запросы; Codex оформлял и исправлял заметки по сохранённым
ответам. Это не автономный успешный проход оформления графа Goose.
Ошибочные черновики — reports/literature_formatting_*/,
reports/literature2_codex_review/, reports/final_review_before/.

Первый SELECT статей вернул пустой результат, ASK — false: основная точка
Wikidata не содержит научные статьи. Отрицательный ответ не доказывает
неверный класс статьи. Отдельный запрос по найденному понятию
quantum superposition (Q830791) вернул пять свойств; выбран P227 = 4346012-4.
Точный ответ — notes/Запрос_WD_QuantumSuperposition.md, связь — в Модель_exp_gauss.
Ошибочная неподтверждённая подпись Q1293220, добавленная Goose, удалена.

Локальный audit_graph.py возвращает 1 из-за требования исходящих связей у Автор
и Ограничение, которых не предусматривает схема. Проверка не менялась ради нуля.
Итоговые команды и коды — reports/final_checks.json.
""")
print("Recorded personal comments, three thesis verdicts, report and literature acceptance.")
