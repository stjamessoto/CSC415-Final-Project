# RetailLang — End-to-End Demo Walkthrough

This document traces a single RetailLang command through the full compiler
pipeline: raw input → token stream → parse tree → AST → generated code →
output.

---

## Demo Command

```
Load sales.csv, filter by region = West, compute total revenue by product,
and generate a bar chart
```

---

## Stage 1 — Raw Input

The user types the command above into the RetailLang IDE or CLI. The system
receives it as a plain Python string.

```python
command = (
    "Load sales.csv, filter by region = West, "
    "compute total revenue by product, and generate a bar chart"
)
```

---

## Stage 2 — Synonym Resolution

Before tokenisation the input passes through the synonym resolver. In this
command no synonyms are present, so the string is unchanged. If the user had
written `"import sales.csv"` the resolver would replace `import` with `load`.

---

## Stage 3 — Token Stream

The lexer splits the input into a flat list of typed tokens.

```
KEYWORD     load
FILENAME    sales.csv
PUNCT       ,
KEYWORD     filter
KEYWORD     by
IDENTIFIER  region
COMPARATOR  =
STRING      West
PUNCT       ,
KEYWORD     compute
KEYWORD     total
IDENTIFIER  revenue
KEYWORD     by
IDENTIFIER  product
PUNCT       ,
KEYWORD     and
KEYWORD     generate
ARTICLE     a
KEYWORD     bar
KEYWORD     chart
EOF
```

---

## Stage 4 — Parse Tree

The recursive descent parser reads the token stream and produces a concrete
parse tree showing every grammar rule that fired.

```
program
└── compound_stmt
    ├── load_stmt
    │   ├── load_kw         "load"
    │   └── FILENAME        "sales.csv"
    ├── filter_stmt
    │   ├── filter_kw       "filter"
    │   └── condition
    │       ├── column_ref  "region"
    │       ├── comparator  "="
    │       └── value       "West"
    ├── compute_stmt
    │   ├── compute_kw      "compute"
    │   ├── metric_expr
    │   │   ├── agg_func    "total"
    │   │   └── column_ref  "revenue"
    │   └── group_clause
    │       ├── group_kw    "by"
    │       └── column_ref  "product"
    └── chart_stmt
        ├── chart_kw        "generate"
        └── chart_type      "bar chart"
```

---

## Stage 5 — Abstract Syntax Tree (AST)

The parser condenses the parse tree into an AST — only semantically meaningful
nodes are kept.

```json
{
  "type": "Program",
  "body": [
    {
      "type": "LoadStatement",
      "filename": "sales.csv",
      "alias": null
    },
    {
      "type": "FilterStatement",
      "conditions": [
        {
          "column": "region",
          "operator": "=",
          "value": "West"
        }
      ]
    },
    {
      "type": "ComputeStatement",
      "aggregation": "sum",
      "column": "revenue",
      "group_by": ["product"]
    },
    {
      "type": "ChartStatement",
      "chart_type": "bar",
      "x": "product",
      "y": "revenue",
      "title": "Total revenue by product"
    }
  ]
}
```

---

## Stage 6 — Generated Pandas Code

The executor walks the AST and emits the following Python script.

```python
import pandas as pd
import plotly.express as px

# Load
df = pd.read_csv("sales.csv")

# Filter
df = df[df["region"] == "West"]

# Compute
result = df.groupby("product")["revenue"].sum().reset_index()
result.columns = ["product", "revenue"]

# Chart
fig = px.bar(
    result,
    x="product",
    y="revenue",
    title="Total revenue by product",
    template="plotly_white",
)
fig.show()
```

---

## Stage 7 — Generated SQL (alternate output)

```sql
SELECT
    product,
    SUM(revenue) AS total_revenue
FROM sales
WHERE region = 'West'
GROUP BY product
ORDER BY total_revenue DESC;
```

---

## Stage 8 — Final Output

The bar chart renders in the RetailLang IDE live preview panel showing total
revenue per product for the West region. The generated Pandas and SQL code
appear in the "Generated code" tab for the user to copy or download.

---

## Error Demo

If the user makes a typo:

```
Load sales.csv and comptue total revenue by region
```

The lexer flags `comptue` as an unrecognised token and the IDE shows:

```
LexError: Unknown keyword 'comptue' at position 22.
Did you mean: 'compute'?
```

The suggestion is computed using Levenshtein edit distance against the known
keyword vocabulary.