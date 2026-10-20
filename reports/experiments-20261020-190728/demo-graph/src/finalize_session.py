import os
from pathlib import Path

# 1. Rename task file and update references
old_task = Path('tasks/Обработать данные и проверить линейность ln k от 1/T.md')
new_task = Path('tasks/Линейность Аррениуса.md')

if old_task.exists():
    old_task.rename(new_task)

# Update links in other task files
for tf in Path('tasks').glob('*.md'):
    content = tf.read_text(encoding='utf-8')
    if '[[Обработать данные и проверить линейность ln k от 1/T]]' in content:
        content = content.replace('[[Обработать данные и проверить линейность ln k от 1/T]]', '[[Линейность Аррениуса]]')
        tf.write_text(content, encoding='utf-8')

# 2. Close main task
main_task = Path('tasks/Проверить закон Аррениуса и найти энергию активации.md')
if main_task.exists():
    content = main_task.read_text(encoding='utf-8')
    summary = "\n\n## Итог\nЗакон Аррениуса подтвержден (R^2 = 0.9993).\nЭнергия активации E_a = 51.66 кДж/моль.\nНезависимая проверка (двухточечный приближенный расчет) дала 51.32 кДж/моль, разница 0.66% (< 1%).\nВсе подзадачи выполнены."
    content = content.replace('status: открыта', 'status: выполнена')
    if '## Итог' not in content:
        content = content.replace('## Связи', summary + '\n\n## Связи')
    main_task.write_text(content, encoding='utf-8')

# 3. Write diary
diary_content = """# Diary 2026-10-20
- Запрос: Проверить закон Аррениуса и найти Ea.
- Выполнено: 
  1. Обработка данных (25-70 C), исключение серии 2024-03.
  2. Расчет Ea регрессией: 51.66 кДж/моль.
  3. Приближенная проверка по двум точкам: 51.32 кДж/моль.
- Статусы: Все подзадачи и основная задача переведены в 'выполнена'.
- Граф: Созданы заметки НаборДанных, Эксперимент, Результат, Проверка, Ограничение.
- Команда: python src/calc_ea.py
"""
with open('diary.md', 'w', encoding='utf-8') as f:
    f.write(diary_content)
