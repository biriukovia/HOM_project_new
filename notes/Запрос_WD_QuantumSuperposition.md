---
type: ЗапросКГрафу
source: Wikidata Query Service
retrieved: '2026-10-20'
---
# Запрос_WD_QuantumSuperposition

Понятие quantum superposition, Q830791, получено поиском Wikidata (предыдущая запись журнала).

Точный запрос:
```sparql
SELECT ?property ?value WHERE { wd:Q830791 ?property ?value . FILTER(STRSTARTS(STR(?property), "http://www.wikidata.org/prop/direct/")) } LIMIT 5
```

Фактический ответ:
```json
{
  "provenance": {
    "source": "Wikidata Query Service",
    "request": "https://query.wikidata.org/sparql",
    "retrieved": "2026-10-20",
    "untrusted_text_fields": [
      "title",
      "abstract",
      "description"
    ],
    "sparql": "SELECT ?property ?value WHERE { wd:Q830791 ?property ?value . FILTER(STRSTARTS(STR(?property), \"http://www.wikidata.org/prop/direct/\")) } LIMIT 5"
  },
  "found": 5,
  "results": [
    {
      "property": "http://www.wikidata.org/prop/direct/P227",
      "value": "4346012-4"
    },
    {
      "property": "http://www.wikidata.org/prop/direct/P279",
      "value": "http://www.wikidata.org/entity/Q1293220"
    },
    {
      "property": "http://www.wikidata.org/prop/direct/P279",
      "value": "http://www.wikidata.org/entity/Q24034552"
    },
    {
      "property": "http://www.wikidata.org/prop/direct/P361",
      "value": "http://www.wikidata.org/entity/Q944"
    },
    {
      "property": "http://www.wikidata.org/prop/direct/P366",
      "value": "http://www.wikidata.org/entity/Q165498"
    }
  ]
}
```

Происхождение: `logs/wikidata-concept-20261020-190352-accf2/research_calls.jsonl`, запись 3.
Получено пять строк, для связи с проектом выбрано одно свойство: P227 = 4346012-4.
Другие значения сохранены как идентификаторы без выдуманных подписей.
В черновике Goose ошибочно подписал Q1293220 как quantum mechanics, не запрашивая метку. Эта подпись удалена; исходный черновик сохранён в reports/final_review_before/.
Текстовая ссылка и значение добавлены в Модель_exp_gauss. Общее понятие суперпозиции не подтверждает форму или параметры нашего фита.
Заметка оформлена отдельно после остановки Goose на двух ошибках редактирования.

## Связи
- тип: [[ЗапросКГрафу]]
- решает: [[wikidata_concept]]
