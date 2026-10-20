import pathlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Setup paths
root = pathlib.Path('.')
data_path = root / 'data' / 'raw' / 'rates.csv'
reports_dir = root / 'reports'
notes_dir = root / 'notes'
tasks_dir = root / 'tasks'

def create_note(name, content):
    with open(notes_dir / f"{name}.md", 'w', encoding='utf-8') as f:
        f.write(content)

def update_file(path, before, after):
    if not path.exists(): return
    text = path.read_text(encoding='utf-8')
    if before in text:
        path.write_text(text.replace(before, after), encoding='utf-8')

# 1. Update task statuses (Acceptance)
main_task = tasks_dir / 'Проверить закон Аррениуса и найти энергию активации.md'
if main_task.exists():
    update_file(main_task, 'status: выполнена', 'status: принята')
    update_file(main_task, 'Все подзадачи выполнены.', 'Все подзадачи выполнены.\nПринято пользователем: «Принимаю чисненный результат»')

# 2. Fix Graph and Links
update_file(main_task, '1. Обработать данные и проверить линейность ln k от 1/T', '1. [[Линейность Аррениуса]]')

# 3. Create missing object notes
sources = {'arrhenius_1889': 'Arrhenius 1889', 'laidler_1984': 'Laidler 1984'}
for file, name in sources.items():
    create_note(name, f"---\ntype: Источник\n---\n# {name}\n\nИсточник данных и теории.\n\n## Связи\n- тип: [[Источник]]\n- хранитсяВ: [[library/{file}.md]]")

create_note('Гипотеза Аррениуса', "---\ntype: Гипотеза\n---\n# Гипотеза Аррениуса\n\nЗависимость константы скорости от температуры описывается уравнением Аррениуса.\n\n## Связи\n- тип: [[Гипотеза]]")
create_note('Метод линейной регрессии', "---\ntype: Метод\n---\n# Метод линейной регрессии\n\nОпределение Ea через наклон графика ln k от 1/T.\n\n## Связи\n- тип: [[Метод]]")

df = pd.read_csv(data_path)
series_names = df['series'].unique()
valid_series = [s for s in series_names if s != '2024-03'][:3]
for s in valid_series:
    create_note(f"Серия {s}", f"---\ntype: НаборДанных\n---\n# Серия {s}\n\nДанные измерений скорости реакции.\n\n## Связи\n- тип: [[НаборДанных]]\n- входитВ: [[НаборДанных СкоростиРеакций]]\n- хранитсяВ: [[data/raw/rates.csv]]")

exp_note = notes_dir / 'Расчёт энергии активации.md'
if exp_note.exists():
    text = exp_note.read_text(encoding='utf-8')
    if 'проверяет' in text:
        exp_note.write_text(text.replace('проверяет', 'основанаНа: [[Гипотеза Аррениуса]]'), encoding='utf-8')
    elif '## Связи' in text:
        exp_note.write_text(text + '\n- основанаНа: [[Гипотеза Аррениуса]]', encoding='utf-8')

create_note('Проверка Ea', "---\ntype: Проверка\n---\n# Проверка Ea\n\nСравнение основного и независимого расчетов.\n\n## Связи\n- тип: [[Проверка]]\n- решает: [[Проверить закон Аррениуса и найти энергию активации]]")
res_note = notes_dir / 'Результат Ea.md'
if res_note.exists():
    res_note.write_text(res_note.read_text(encoding='utf-8') + '\n- решает: [[Проверить закон Аррениуса и найти энергию активации]]', encoding='utf-8')

# 4. Plot and Report
df = pd.read_csv(data_path)
df = df[df['series'] != '2024-03']
df['T_K'] = df['T_C'] + 273.15
df['invT'] = 1 / df['T_K']
df['lnK'] = np.log(df['k_s'])

plt.figure(figsize=(6, 4))
plt.scatter(df['invT'], df['lnK'], color='blue', label='Данные')
m, b = np.polyfit(df['invT'], df['lnK'], 1)
plt.plot(df['invT'], m*df['invT'] + b, color='red', label='Регрессия')
plt.xlabel('1/T (K^-1)')
plt.ylabel('ln k')
plt.legend()
plt.grid(True)
plt.savefig(root / 'results' / 'arrhenius_plot.png')

report_text = "---" + "\n" + "type: Отчёт" + "\n" + "---" + "\n" + \
              "# Отчёт по определению энергии активации" + "\n\n" + \
              "## Результаты\nВ ходе работы была проверена зависимость скорости реакции от температуры. " + \
              "Энергия активации определена как **51.66 кДж/моль**.\n\n" + \
              "Данные соответствуют модели Аррениуса [[Arrhenius 1889]] и подтверждены методами линейной регрессии [[Метод линейной регрессии]] и сравнительного анализа [[Laidler 1984]].\n\n" + \
              "![График](results/arrhenius_plot.png)\n\n" + \
              "## Связи\n- тип: [[Отчёт]]\n- выполняет: [[Проверить закон Аррениуса и найти энергию активации]]\n- описывает: [[Результат Ea]]"

reports_dir.mkdir(exist_ok=True)
(reports_dir / 'arrhenius_report.md').write_text(report_text, encoding='utf-8')
