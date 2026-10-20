---
type: ЗапросКГрафу
source: Wikidata
retrieved: '2026-10-20'
---
# Wikidata_первый_опыт

Реальные пустые/отрицательные результаты сохранены ниже.

Основная точка SPARQL не содержит научных статей (это указано в описании инструмента). ASK=false для Q51575871 не доказывает, что статья не относится к указанному классу; вывод Goose исправлен. Поиск сущности и SPARQL обращаются к разным наборам данных. Это не завершённое получение свойства понятия HOM.

Происхождение: `logs/literature2-20261020-185054-c7617/research_calls.jsonl`.

### Запись 5: wikidata_search
```json
{
  "arguments": {
    "text": "Hong-Ou-Mandel effect",
    "language": "ru",
    "limit": 5
  },
  "response": {
    "provenance": {
      "source": "Wikidata",
      "request": "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Hong-Ou-Mandel+effect&language=ru&uselang=ru&limit=5&format=json",
      "retrieved": "2026-10-20",
      "untrusted_text_fields": [
        "title",
        "abstract",
        "description"
      ]
    },
    "results": []
  }
}
```

### Запись 6: wikidata_search
```json
{
  "arguments": {
    "text": "Hong-Ou-Mandel effect",
    "language": "en",
    "limit": 5
  },
  "response": {
    "provenance": {
      "source": "Wikidata",
      "request": "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Hong-Ou-Mandel+effect&language=en&uselang=en&limit=5&format=json",
      "retrieved": "2026-10-20",
      "untrusted_text_fields": [
        "title",
        "abstract",
        "description"
      ]
    },
    "results": []
  }
}
```

### Запись 7: wikidata_search
```json
{
  "arguments": {
    "text": "Hong-Ou-Mandel",
    "language": "en",
    "limit": 5
  },
  "response": {
    "provenance": {
      "source": "Wikidata",
      "request": "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Hong-Ou-Mandel&language=en&uselang=en&limit=5&format=json",
      "retrieved": "2026-10-20",
      "untrusted_text_fields": [
        "title",
        "abstract",
        "description"
      ]
    },
    "results": [
      {
        "id": "Q51575871",
        "label": "Hong-Ou-Mandel interference of two phonons in trapped ions.",
        "description": "scientific article published in November 2015"
      },
      {
        "id": "Q35541068",
        "label": "Hong-Ou-Mandel experiment for temporal investigation of single-electron fractionalization.",
        "description": "scientific article published on 21 April 2015"
      },
      {
        "id": "Q57154798",
        "label": "Hong-Ou-Mandel Interference between Two Deterministic Collective Excitations in an Atomic Ensemble",
        "description": "scientific article published in Physical Review Letters"
      },
      {
        "id": "Q61157253",
        "label": "Hong-Ou-Mandel interference between triggered and heralded single photons from separate atomic systems",
        "description": null
      },
      {
        "id": "Q84502976",
        "label": "Hong-Ou-Mandel dip measurements of polarization-entangled photon pairs at 1550 nm",
        "description": "scientific article published on 01 April 2010"
      }
    ]
  }
}
```

### Запись 8: wikidata_sparql
```json
{
  "arguments": {
    "query": "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q13442814 . SERVICE wikibase:label { bd:serviceParam wikibase:language \"en,ru\". } } LIMIT 10",
    "limit": 50
  },
  "response": {
    "provenance": {
      "source": "Wikidata Query Service",
      "request": "https://query.wikidata.org/sparql",
      "retrieved": "2026-10-20",
      "untrusted_text_fields": [
        "title",
        "abstract",
        "description"
      ],
      "sparql": "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q13442814 . SERVICE wikibase:label { bd:serviceParam wikibase:language \"en,ru\". } } LIMIT 10"
    },
    "found": 0,
    "results": []
  }
}
```

### Запись 9: wikidata_sparql
```json
{
  "arguments": {
    "query": "ASK { wd:Q51575871 wdt:P31 wd:Q13442814 . }",
    "limit": 50
  },
  "response": {
    "provenance": {
      "source": "Wikidata Query Service",
      "request": "https://query.wikidata.org/sparql",
      "retrieved": "2026-10-20",
      "untrusted_text_fields": [
        "title",
        "abstract",
        "description"
      ],
      "sparql": "ASK { wd:Q51575871 wdt:P31 wd:Q13442814 . }"
    },
    "found": 1,
    "results": [
      {
        "ask": false
      }
    ]
  }
}
```


## Связи
- тип: [[ЗапросКГрафу]]
- решает: [[literature_search_2]]
