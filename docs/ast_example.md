# RetailLang — AST Node Reference

This document defines every AST node type produced by the RetailLang parser,
with field definitions and a JSON example for each.

---

## ProgramNode

The root node. Every parsed input produces exactly one `ProgramNode`.

| Field    | Type            | Description                        |
|----------|-----------------|------------------------------------|
| `type`   | `"Program"`     | Node discriminator                 |
| `body`   | `list[ASTNode]` | Ordered list of top-level statements |

```json
{
  "type": "Program",
  "body": [ ]
}
```

---

## LoadStatement

Produced by: `load sales.csv`, `import orders.csv as o`

| Field      | Type            | Description                          |
|------------|-----------------|--------------------------------------|
| `type`     | `"LoadStatement"` | Node discriminator                 |
| `filename` | `str`           | Path to the file                     |
| `alias`    | `str \| null`   | Optional in-memory name for the dataset |

```json
{
  "type": "LoadStatement",
  "filename": "sales.csv",
  "alias": null
}
```

---

## FilterStatement

Produced by: `filter by region = West`, `where profit > 1000`

| Field        | Type              | Description                      |
|--------------|-------------------|----------------------------------|
| `type`       | `"FilterStatement"` | Node discriminator             |
| `conditions` | `list[Condition]` | One or more filter conditions    |
| `bool_op`    | `"and" \| "or"`   | Logical operator between conditions |

### Condition object

| Field      | Type   | Description                              |
|------------|--------|------------------------------------------|
| `column`   | `str`  | Column name to filter on                 |
| `operator` | `str`  | One of `=`, `!=`, `>`, `<`, `>=`, `<=`  |
| `value`    | `str \| float` | Value to compare against       |

```json
{
  "type": "FilterStatement",
  "bool_op": "and",
  "conditions": [
    { "column": "region",   "operator": "=",  "value": "West" },
    { "column": "profit",   "operator": ">=", "value": 500    }
  ]
}
```

---

## ComputeStatement

Produced by: `compute total revenue by product`, `calculate average profit`

| Field         | Type            | Description                          |
|---------------|-----------------|--------------------------------------|
| `type`        | `"ComputeStatement"` | Node discriminator              |
| `aggregation` | `str`           | Canonical agg function: `sum`, `avg`, `count`, `max`, `min` |
| `column`      | `str`           | Column to aggregate                  |
| `group_by`    | `list[str]`     | Zero or more grouping columns        |

```json
{
  "type": "ComputeStatement",
  "aggregation": "sum",
  "column": "revenue",
  "group_by": ["product", "region"]
}
```

---

## ChartStatement

Produced by: `generate a bar chart of revenue by region`

| Field        | Type     | Description                                          |
|--------------|----------|------------------------------------------------------|
| `type`       | `"ChartStatement"` | Node discriminator                       |
| `chart_type` | `str`    | One of `bar`, `line`, `pie`, `scatter`, `histogram`  |
| `x`          | `str`    | Column for the x-axis / labels                       |
| `y`          | `str`    | Column for the y-axis / values                       |
| `title`      | `str \| null` | Optional chart title                            |
| `compare`    | `list[str] \| null` | Columns to compare (multi-series charts) |

```json
{
  "type": "ChartStatement",
  "chart_type": "bar",
  "x": "region",
  "y": "revenue",
  "title": "Total revenue by region",
  "compare": null
}
```

---

## PivotStatement

Produced by: `create a pivot table by product and profit margin`

| Field     | Type     | Description                          |
|-----------|----------|--------------------------------------|
| `type`    | `"PivotStatement"` | Node discriminator           |
| `index`   | `str`    | Row dimension column                 |
| `columns` | `str`    | Column dimension column              |
| `values`  | `str`    | Values to aggregate in cells         |
| `aggfunc` | `str`    | Aggregation: `sum`, `avg`, `count`   |

```json
{
  "type": "PivotStatement",
  "index": "product",
  "columns": "region",
  "values": "revenue",
  "aggfunc": "sum"
}
```

---

## SortStatement

Produced by: `sort by revenue descending`

| Field      | Type      | Description                          |
|------------|-----------|--------------------------------------|
| `type`     | `"SortStatement"` | Node discriminator           |
| `column`   | `str`     | Column to sort by                    |
| `direction`| `"asc" \| "desc"` | Sort direction               |

```json
{
  "type": "SortStatement",
  "column": "revenue",
  "direction": "desc"
}
```

---

## Full Multi-Statement AST Example

Input:
```
Load orders.csv, filter by category = Electronics and profit >= 200,
compute average profit by region, sort by profit descending,
and generate a bar chart
```

AST output:
```json
{
  "type": "Program",
  "body": [
    {
      "type": "LoadStatement",
      "filename": "orders.csv",
      "alias": null
    },
    {
      "type": "FilterStatement",
      "bool_op": "and",
      "conditions": [
        { "column": "category", "operator": "=",  "value": "Electronics" },
        { "column": "profit",   "operator": ">=", "value": 200 }
      ]
    },
    {
      "type": "ComputeStatement",
      "aggregation": "avg",
      "column": "profit",
      "group_by": ["region"]
    },
    {
      "type": "SortStatement",
      "column": "profit",
      "direction": "desc"
    },
    {
      "type": "ChartStatement",
      "chart_type": "bar",
      "x": "region",
      "y": "profit",
      "title": "Average profit by region",
      "compare": null
    }
  ]
}
```