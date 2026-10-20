import yaml
import os

with open('ontology.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

classes = data['classes']
os.makedirs('ontology', exist_ok=True)

for class_name, info in classes.items():
    content = f"---\nkind: класс\n---\n# {class_name}\n\n{info['definition']}\n\n"
    
    # Relations from this class (domain)
    rels = []
    for prop, p_info in data['properties'].items():
        domain = p_info['domain']
        if isinstance(domain, list):
            if class_name in domain:
                rels.append(prop)
        elif domain == class_name:
            rels.append(prop)
    
    if rels:
        content += "Отношения от этого класса: " + ", ".join(rels) + "\n"
    
    # Attributes (domain)
    attrs = []
    for attr, a_info in data['attributes'].items():
        if a_info['domain'] == class_name:
            attrs.append(f"{attr} ({', '.join(a_info['values'])})")
            
    if attrs:
        content += "Атрибуты: " + ", ".join(attrs) + "\n"
    
    # Links (parent)
    parent = info.get('parent')
    if parent:
        content += "\n## Связи\n- подклассОт: [[{parent}]]\n"
    
    with open(f'ontology/{class_name}.md', 'w', encoding='utf-8') as f:
        f.write(content)
