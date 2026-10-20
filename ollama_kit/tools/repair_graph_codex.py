"""One authorized Codex repair after the failed Goose graph1 experiment.
Does not edit data, checks, ontology.yaml, or previous scientific results.
"""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/week4_codex_repair"

def write(path, text):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")

def note(name, typ, body, links):
    write(f"notes/{name}.md", f"---\ntype: {typ}\n---\n# {name}\n\n{body}\n\n"
          f"## Связи\n- тип: [[{typ}]]\n" +
          "".join(f"- {prop}: [[{target}]]\n" for prop, target in links))

def task(name, request, ready, result, links, status="выполнена"):
    write(f"tasks/{name}.md",
          f"---\ntype: Задача\nstatus: {status}\n---\n# {name}\n\n"
          f"## Запрос пользователя\n{request}\n\n## Готово, когда\n{ready}\n\n"
          "## Не входит\nНовые научные расчёты, изменение данных, онтологии, проверок и личная приёмка.\n\n"
          f"## Итог\n{result}\n\n## Связи\n- тип: [[Задача]]\n" +
          "".join(f"- {p}: [[{t}]]\n" for p, t in links))

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    for folder in ("notes", "ontology", "tasks", ".obsidian"):
        if (ROOT/folder).exists():
            shutil.copytree(ROOT/folder, OUT/"before"/folder)
    if (ROOT/"fix_graph.py").exists():
        shutil.copy2(ROOT/"fix_graph.py", OUT/"before/fix_graph.py")
    ont = yaml.safe_load((ROOT/"ontology.yaml").read_text(encoding="utf-8"))
    for cls, cfg in ont["classes"].items():
        props = [p for p,s in ont["properties"].items()
                 if cls in (s["domain"] if isinstance(s["domain"],list) else [s["domain"]])]
        write(f"ontology/{cls}.md", f"---\nkind: класс\n---\n# {cls}\n\n"
              f"{cfg['definition']}.\n\nИсходящие отношения: {', '.join(props) or 'не заданы'}.\n"
              "\n## Связи\n" + (f"- подклассОт: [[{cfg['parent']}]]\n" if cfg.get("parent") else ""))
    write(".obsidian/app.json", json.dumps({"showUnsupportedFiles":True}, indent=2)+"\n")
    write(".obsidian/graph.json", json.dumps({
        "showAttachments":True, "showOrphans":True, "showArrow":True,
        "colorGroups":[{"query":f"path:{p}", "color":{"a":1,"rgb":c}}
                       for p,c in [("ontology",9474192),("tasks",16761685),
                                   ("notes",5987296),("reports",1153422)]]}, indent=2)+"\n")
    fit = json.loads((ROOT/"results/course_fit.json").read_text(encoding="utf-8"))
    note("Данные_HOM","НаборДанных",
         "130 измеренных пар: координата в сантиметрах и нормированные совпадения. "
         "Однопроходная схема подтверждена владельцем (diary.md, 13.10); ошибки отдельных точек не предоставлены.",
         [("хранитсяВ","data/data.txt")])
    for name, body in [
        ("Модель_exp_gauss","Экспонента, свёрнутая с гауссовым распределением разности времён испускания. "
         "Функции m_exp_gauss и kernel_exp_gauss. Параметр V отличается от глубины V0."),
        ("Модель_coherent","Когерентно сформированный волновой пакет: квадрат нормированного перекрытия. "
         "Функция m_exp_gauss_coherent; здесь V соответствует видности при нулевой задержке."),
        ("Модель_exp_laplace","Экспонента, свёрнутая с распределением Лапласа. "
         "Функции m_exp_laplace и kernel_exp_laplace. Это альтернативная модель сохранённого анализа.")]:
        note(name,"Модель",body,[("реализованВ","src/hom_models.py"),
                               ("имеетОграничение","Ограничение_физика")])
    links=[("реализованВ","src/quick_fit.py"),("используетДанные","Данные_HOM"),
           ("используетМодель","Модель_exp_gauss"),("даёт","Результат_course_fit")]
    note("Процедура_короткого_фита","Расчёт",
         "Один МНК-фит exp*gauss, без bootstrap. В этой работе повторно не запускался; "
         "проверяется ранее сохранённый результат.",links)
    # The first Goose pass also created this name; retain it as an explicit alias object.
    note("Расчёт_quick_fit","Расчёт",
         "Заметка первого прохода Goose о той же процедуре, что «Процедура_короткого_фита». "
         "Это не второй запуск и не независимый результат.",links)
    note("Результат_course_fit","Результат",
         f"Сохранённый учебный результат: V0={fit['derived']['V0']:.12f}, "
         f"T1={fit['derived']['T1_ps']:.9f} пс; RSS={fit['rss']:.12g}. "
         "T1 имеет условную модельную интерпретацию.",
         [("хранитсяВ","results/course_fit.json"),("имеетОграничение","Ограничение_физика")])
    note("Независимая_проверка","Проверка",
         "checks/check.py сверяет отпечаток данных, числа, независимую формулу и квадратуру. "
         "Проверяет воспроизводимость, а не физическую истинность модели.",
         [("реализованВ","checks/check.py"),("проверяет","Результат_course_fit")])
    note("Полный_результат","Результат",
         "Ранее сохранённый анализ семи моделей. При данной подготовке не пересчитывается.",
         [("хранитсяВ","results/fit_results.json"),("имеетОграничение","Ограничение_физика")])
    note("График_HOM","Результат",
         "Существующий график основного HOM-фита из прежнего исследования. Новый график не строился.",
         [("хранитсяВ","results/fig_fit_main.png")])
    note("Ограничение_физика","Ограничение",
         "Не предоставлены абсолютная калибровка совпадений, ошибки отдельных точек, "
         "независимые g²(0), T1 и коэффициенты светоделителя. Фит не заменяет эти измерения. "
         "У этого класса нет исходящих отношений в ontology.yaml; входящие связи имеютОграничение "
         "ведут от моделей и результатов.",[])
    note("Отчёт_проверки_графа","Отчёт",
         "Отдельное исправление Codex, разрешённое пользователем после неудачного опыта Goose. "
         "Не является доказательством самостоятельного успеха Goose.",
         [("хранитсяВ","reports/week4_codex_repair/review.md"),
          ("описывает","Независимая_проверка"),("описывает","Результат_course_fit")])
    task("task1","Настройка Obsidian","Конфиги созданы.",
         "Codex исправил настройки и описания 12 классов по неизменной ontology.yaml.",
         [("подзадачаОт","graph_setup")])
    task("task2","Наполнение notes","10 объектов.",
         "Codex исправил заголовки, реальные пути и связи. Созданы 10 разных предметных объектов "
         "первоначального запроса, а также отчёт и явно обозначенная дублирующая заметка процедуры.",
         [("подзадачаОт","graph_setup")])
    task("graph_setup",
         "Включить режим графа, создать структуру Obsidian и заполнить заметки объектов.",
         "Созданы конфиги, заметки классов и 10+ объектов.",
         "Первый опыт Goose и попытка исправления не прошли проверку. Пользователь разрешил "
         "отдельное исправление Codex; оно выполнено. Ограничение локального аудитора описано "
         "в отчёте. Личная приёмка ожидается.",
         [("результатЗадачи","Отчёт_проверки_графа"),("результатЗадачи","Независимая_проверка")])
    sub=ROOT/"tasks/Подготовка сдачи.md"
    text=sub.read_text(encoding="utf-8")
    text=text.replace("- тип: [[Задача]]","- тип: [[Задача]]\n- результатЗадачи: [[Отчёт_проверки_графа]]")
    sub.write_text(text,encoding="utf-8")
    review = """# Граф HOM после отдельного исправления Codex

Дата: 20.10.2026. Пользователь разрешил отдельное исправление заметок.
Первый проход Goose и его попытка исправления не прошли проверку; исходное
состояние сохранено в before/, полный экспорт — в logs/graph1-20261020-181201-3159d/.
Это не самостоятельный успешный опыт Goose.

Исправлены YAML, реальные пути, описания классов, задачи и настройки Obsidian.
Проверки и ontology.yaml не изменялись.
У класса Ограничение нет исходящих отношений; он связан входящими
имеетОграничение от моделей и результатов. Требование локального audit_graph.py
об исходящей связи у каждого объекта здесь не соответствует схеме.
Этот недостаток не исправляется вымышленной связью.

Числовая проверка подтверждает воспроизводимость, не истинность модели.
Личная сверка и приёмка ожидаются.

```mermaid
graph LR
  D[Данные HOM] -->|хранитсяВ| F[data/data.txt]
  C[Короткий фит] -->|используетДанные| D
  C -->|используетМодель| M[exp*gauss]
  C -->|даёт| R[Учебный результат]
  V[Независимая проверка] -->|проверяет| R
  R -->|имеетОграничение| L[Недостающие независимые измерения]
  M -->|имеетОграничение| L
```
"""
    # The report must exist before the graph audit resolves its file edge.
    write("reports/week4_codex_repair/review.md",review)
    records=[]
    for args in [["checks/check.py"],["ollama_kit/tools/audit_graph.py","."]]:
        p=subprocess.run([sys.executable,"-X","utf8",*args],cwd=ROOT,capture_output=True,
                         text=True,encoding="utf-8")
        records.append({"command":"python "+" ".join(args),"exit_code":p.returncode,
                        "stdout":p.stdout,"stderr":p.stderr})
    write("reports/week4_codex_repair/checks.json",json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(records,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
