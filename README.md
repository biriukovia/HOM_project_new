# AI4Science: домашняя работа недель 1–5, проект HOM

Состояние на 20.10.2026. Здесь собраны реальные запуски, выполненные ноутбуки,
проверки и личные решения владельца. Помощь Codex, работа Goose и проверки
человека указаны отдельно. Окончательный зачёт определяет преподаватель.

## Соответствие заданий файлам

| Неделя и требование | Свидетельства | Фактический итог |
|---|---|---|
| 1. Маленькая задача и независимая проверка | [AGENTS](AGENTS.md), [quick_fit](src/quick_fit.py), [результат](results/course_fit.json), [экспорт](reports/hom-fit-20261020-095009/), [журнал](diary.md) | Существующий фит проходит checks/check.py, код 0; успешный опыт не повторён |
| 2. Без договора / с договором | [проверки](reports/week2_independent_checks.json), [без AGENTS](reports/experiments-20261020-190728/w2-without/), [с AGENTS](reports/experiments-20261020-190728/w2-with/) | Коды 1 и 0; одна модель Gemma; ошибки сохранены |
| 2. Договор и проверка своего проекта | [AGENTS](AGENTS.md), [checks](checks/), [самотест](reports/check_selftest.txt) | Узкая цель, фиксированный вход, независимый критерий и отрицательные контроли |
| 3. Ноутбук, разделы 0–12 | [выполненный ноутбук](ollama_kit/week3/agent_loop_ollama.ipynb), [своя задача](logs/week3-notebook-20261020-173454-7b421/), [дозапуск](logs/week3-resume-20261020-185649/) | my_phi=True, 6 итераций; завершены отсутствовавшее сравнение моделей и прерванные 32 опыта защиты |
| 3. Полная статья, ответы и контекст | [аудит опыта](reports/week3_evidence.md), [экспорт](logs/paper-20261020-185355-e18ae/), [полнота чтения](reports/week3_full_read_verification.json) | Прочитаны 48 672 символа; /status 25 197 / 32 768; личный вердикт и найденная ошибка формулы записаны раздельно |
| 3. L1→L2→L3 и сверка | [L1](memory/L1.md), [L2 с таблицей](memory/L2.md), [L3](memory/L3.md), [происхождение](memory/PROVENANCE.md) | Ручной каскад в раздельных контекстах; пользователь подтвердил тезисы 10,4,8, цитаты перенёс Codex из PDF |
| 3. Вынесенный контекст и INDEX | [INDEX](INDEX.md), [контекстные опыты](reports/experiments-20261020-190728/), [сессия INDEX](logs/index-20261020-175912-cc88f/) | Однопроходная схема найдена в обоих вариантах; функция найдена по INDEX одним вызовом |
| 4. Демонстрация в двух сессиях | [комплект Аррениуса](reports/experiments-20261020-190728/demo-graph/), [отчёт с графиком](reports/experiments-20261020-190728/demo-graph/reports/arrhenius_report.md), [пересчёт](reports/week4_demo_checks.json) | Ea=51.6625787854 кДж/моль; численная проверка 0; результат и отчёт приняты |
| 4. Своя онтология, ≥10 объектов, две сессии | [схема](ontology.yaml), [классы](ontology/), [объекты](notes/), [задачи](tasks/), [.obsidian](.obsidian/), [graph1](logs/graph1-20261020-181201-3159d/), [graph2](logs/graph2-20261020-182143-4f6f0/) | Граф исправлен Codex после неудачи Goose; граф и [отчёт HOM](reports/course_summary.md) приняты; пользователь проверил ссылки в Obsidian |
| 5. Поисковый ноутбук и смена запросов | [ноутбук](ollama_kit/week5/search_lab_hom.ipynb), [сравнение запросов](reports/search_query_comparison.json), [журнал](logs/week5-notebook-20261020-184616/) | Основные расчёты и SPARQL выполнены; дополнительный запрос получил HTTP 429 |
| 5. Библиотека, пять запросов и оценок | [20 работ](library_search/my_library.json), [ранжирования](library_search/rankings.json), [личные комментарии](reports/my_search_report.md) | Все пять комментариев перенесены дословно из ответа пользователя |
| 5. MCP, ≥5 источников, внешнее понятие | [литература](reports/literature_collection.md), [сверка DOI](reports/personal_doi_review.md), [Wikidata](notes/Запрос_WD_QuantumSuperposition.md) | Пять источников с авторами и provenance; успешный SELECT для Q830791; сбор принят |

Оригинальные задания — docs/week_*_practice.md. Файлы в course/week3/ и
course/week5/ — прежние учебные версии; выполненные копии для сдачи находятся
в ollama_kit/week3/ и ollama_kit/week5/. ollama_kit/examples/ содержит
предоставленные образцы, а не наши выполненные опыты.

## Команды и границы проверок

В подготовленном Windows-окружении, из корня:

```powershell
.\.venv-course\Scripts\python.exe -X utf8 checks/check.py
.\.venv-course\Scripts\python.exe -X utf8 ollama_kit/tools/audit_graph.py .
.\.venv-course\Scripts\python.exe -X utf8 ollama_kit/tools/audit_submission.py
git status --short
```

Фактические команды, выводы и коды — [final_checks.json](reports/final_checks.json).
Численная проверка HOM — **0**. Локальные аудиторы — **1**: причины перечислены
в [submission_audit.md](reports/submission_audit.md), коды не скрыты.
Отсутствующие официальные check_week3.py/check_week4.py разрешено пропустить
организаторами **по сообщению пользователя**. Ollama также разрешена.
Локальные аудиторы не являются официальными проверками курса.

Все агентные опыты этого продолжения выполнялись установленным Goose:

```powershell
.\.venv-course\Scripts\python.exe -X utf8 ollama_kit/run_goose.py <этап> --model gemma4:31b-cloud --agent-dir C:/Users/yury_/AI4Science
```

В сравнении моделей ноутбука 3 использованы также qwen3:8b и qwen3:4b с
разрешения пользователя. run.json, session.json, session.md и research_calls.jsonl
сохраняют фактическую работу, включая ошибки. Код выхода Goose 0 сам по себе
не означает успех задания. Инструкция среды — [START_HERE](ollama_kit/START_HERE.md),
зависимости — [requirements](ollama_kit/requirements.txt).

Повторять успешные опыты для просмотра результатов не нужно. Скрипты repair_*,
record_* и finish_literature_notes.py сохраняют одноразовые действия оформления;
повторный запуск может перезаписать принятые документы. Большие HOM-расчёты
и cascade.sh не входят в команды проверки сдачи.

## Git и ограничения

Сессии собственного графа: коммиты 4fc247c и 109ca04. Демонстрация:
98826b5, 038924f, приёмка e70ad11. Её история сохранена в
[history.bundle](reports/experiments-20261020-190728/demo-graph/history.bundle).
Основной проект содержит последующие коммиты ноутбука 3, недели 5 и итоговой
документации; актуальные идентификаторы показывает git log --oneline.

HOM-данные, прежние результаты, научная статья, ontology.yaml и проверки
не менялись ради успеха. Хеши и проверка известных секретов/шаблонов токенов —
[delivery_integrity.json](reports/delivery_integrity.json). Воспроизводимость
чисел не устанавливает истинность физической модели.
PDF корректуры исключён из Git, но текст статьи присутствует в журнале опыта
чтения. Условия публичного распространения определяет владелец.

Оставшиеся действия — [remaining_user_actions.md](reports/remaining_user_actions.md).
Репозиторий не опубликован; ссылку и доступ преподавателю обеспечивает владелец.
