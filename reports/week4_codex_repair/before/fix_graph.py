import os, yaml, json

# Load ontology
with open('ontology.yaml', 'r', encoding='utf-8') as f:
    ont = yaml.safe_load(f)
classes = ont['classes']

# 1. Fix Class Notes
for name, data in classes.items():
    with open(f'ontology/{name}.md', 'w', encoding='utf-8') as f:
        f.write(f'---\ntype: Класс\n---\nопределение: {data["definition"]}')

# 2. Obsidian Configs
app_json = {'showUnsupportedFiles': True, 'showAttachments': True}
graph_json = {'showArrow': True, 'colors': {'folders': True}}
with open('.obsidian/app.json', 'w', encoding='utf-8') as f: json.dump(app_json, f)
with open('.obsidian/graph.json', 'w', encoding='utf-8') as f: json.dump(graph_json, f)

# 3. Objects
objects = {
    'Данные_HOM': {'type': 'НаборДанных', 'links': {'хранитсяВ': '[[data/data.txt]]'}, 'desc': 'Экспериментальные данные HOM-скана.'},
    'Модель_exp_gauss': {'type': 'Модель', 'links': {'реализованВ': '[[src/hom_models.py]]'}, 'desc': 'Модель exp*gauss.'},
    'Модель_coherent': {'type': 'Модель', 'links': {'реализованВ': '[[src/hom_models.py]]'}, 'desc': 'Модель coherent.'},
    'Модель_exp_laplace': {'type': 'Модель', 'links': {'реализованВ': '[[src/hom_models.py]]'}, 'desc': 'Модель exp*laplace.'},
    'Процедура_короткого_фита': {'type': 'Расчёт', 'links': {'реализованВ': '[[src/quick_fit.py]]', 'используетДанные': '[[Данные_HOM]]', 'используетМодель': '[[Модель_exp_gauss]]', 'даёт': '[[Результат_course_fit]]'}, 'desc': 'Быстрый фит курса.'},
    'Результат_course_fit': {'type': 'Результат', 'links': {'хранитсяВ': '[[results/course_fit.json]]', 'имеетОграничение': '[[Ограничение_физика]]'}, 'desc': 'Численный результат course_fit.'},
    'Независимая_проверка': {'type': 'Проверка', 'links': {'реализованВ': '[[checks/check.py]]', 'проверяет': '[[Результат_course_fit]]'}, 'desc': 'Проверка воспроизводимости.'},
    'Полный_результат': {'type': 'Результат', 'links': {'хранитсяВ': '[[results/full_fit.json]]'}, 'desc': 'Исходный полный результат исследования.'},
    'График_HOM': {'type': 'Результат', 'links': {'хранитсяВ': '[[results/hom_plot.png]]'}, 'desc': 'График зависимости совпадений.'},
    'Ограничение_физика': {'type': 'Ограничение', 'links': {}, 'desc': 'Ограничение физической интерпретации параметров.'}
}

for name, data in objects.items():
    # Correct YAML frontmatter: avoid mixed list/dict in top level of frontmatter
    content = f'---\ntype: {data["type"]}\n---\n- тип: [[{data["type"]}]]\n{data["desc"]}\n'
    for k, v in data['links'].items():
        content += f'- {k}: {v}\n'
    with open(f'notes/{name}.md', 'w', encoding='utf-8') as f: f.write(content)

# 4. Tasks
task_main = {
    'type': 'Задача', 'status': 'выполнена', 
    'запрос': 'Включить режим графа, создать структуру Obsidian и заполнить заметки объектов.', 
    'готово': 'Созданы конфиги, заметки классов и 10+ объектов.', 
    'не_входит': 'новые расчеты', 
    'итог': 'Граф построен, аудит запущен.',
    'результатЗадачи': '[[Независимая_проверка]]'
}
with open('tasks/graph_setup.md', 'w', encoding='utf-8') as f:
    # Task requires - тип: [[Задача]] and ## Итог
    f.write(f'---\ntype: {task_main["type"]}\nstatus: {task_main["status"]}\n---\n- тип: [[Задача]]\nЗапрос пользователя: {task_main["запрос"]}\nГотово когда: {task_main["готово"]}\nНе входит: {task_main["не_входит"]}\n\n## Итог\n{task_main["итог"]}\n- результатЗадачи: {task_main["результатЗадачи"]}\n')

with open('tasks/task1.md', 'w', encoding='utf-8') as f:
    f.write(f'---\ntype: Задача\nstatus: выполнена\n---\n- тип: [[Задача]]\nЗапрос пользователя: Настройка Obsidian\n- подзадачаОт: [[graph_setup]]\n\n## Итог\nКонфиги созданы\n')
with open('tasks/task2.md', 'w', encoding='utf-8') as f:
    f.write(f'---\ntype: Задача\nstatus: выполнена\n---\n- тип: [[Задача]]\nЗапрос пользователя: Наполнение notes\n- подзадачаОт: [[graph_setup]]\n\n## Итог\n10 объектов создано\n')
