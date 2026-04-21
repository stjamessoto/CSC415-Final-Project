# RetailLang Grammar Specification (BNF/EBNF)

## Overview

RetailLang is a domain-specific language (DSL) designed for retail business
analytics. It allows non-technical business stakeholders to describe analytics
tasks in plain English. The grammar is intentionally English-like and tolerates
natural language synonyms for common terms.

---

## EBNF Notation Key

```
::=     definition
|       alternation
[ ]     optional
{ }     zero or more repetitions
( )     grouping
" "     terminal string (literal keyword)
UPPER   non-terminal symbol
```

---

## Top-Level Program

```ebnf
program         ::= statement { statement }

statement       ::= load_stmt
                  | compute_stmt
                  | filter_stmt
                  | chart_stmt
                  | pivot_stmt
                  | sort_stmt
                  | group_stmt
                  | compound_stmt

compound_stmt   ::= statement { "," statement }
                  | statement { "and" statement }
```

---

## Load Statement

```ebnf
load_stmt       ::= load_kw FILENAME [ "as" IDENTIFIER ]

load_kw         ::= "load" | "import" | "read" | "open"

FILENAME        ::= STRING_LITERAL
                  | IDENTIFIER "." file_ext

file_ext        ::= "csv" | "xlsx" | "json" | "parquet"
```

### Examples
```
Load sales.csv
Import orders.csv as orders
Read products.csv
```

---

## Compute Statement

```ebnf
compute_stmt    ::= compute_kw metric_expr [ group_clause ]

compute_kw      ::= "compute" | "calculate" | "find" | "get" | "show"

metric_expr     ::= agg_func column_ref
                  | agg_func "(" column_ref ")"

agg_func        ::= "total"   | "sum"
                  | "average" | "avg" | "mean"
                  | "count"   | "number of"
                  | "max"     | "maximum"
                  | "min"     | "minimum"

column_ref      ::= IDENTIFIER
                  | column_synonym

column_synonym  ::= "revenue"  | "sales"   | "income"
                  | "profit"   | "earnings" | "margin"
                  | "units"    | "quantity" | "qty"
                  | "cost"     | "expense"  | "spend"
                  | "orders"   | "transactions"

group_clause    ::= group_kw column_ref { "," column_ref }

group_kw        ::= "by" | "grouped by" | "per" | "for each"
```

### Examples
```
Compute total revenue by region
Calculate average profit per product
Find total units grouped by category
Show count of orders by month
```

---

## Filter Statement

```ebnf
filter_stmt     ::= filter_kw condition { bool_op condition }

filter_kw       ::= "filter" | "where" | "only" | "select"

condition       ::= column_ref comparator value
                  | column_ref "between" value "and" value
                  | column_ref "in" "(" value_list ")"

comparator      ::= "="  | "==" | "is"
                  | "!=" | "is not" | "not"
                  | ">"  | "greater than"
                  | "<"  | "less than"
                  | ">=" | "at least"
                  | "<=" | "at most"

value           ::= NUMBER | STRING_LITERAL | IDENTIFIER

value_list      ::= value { "," value }

bool_op         ::= "and" | "or"
```

### Examples
```
Filter by region = West
Where profit > 1000
Only region in (East, West, North)
Filter by category = Electronics and profit >= 500
```

---

## Chart Statement

```ebnf
chart_stmt      ::= chart_kw chart_type [ chart_data_clause ] [ title_clause ]

chart_kw        ::= "generate" | "create" | "make" | "plot" | "show" | "draw"

chart_type      ::= "bar chart"   | "bar graph"
                  | "line chart"  | "line graph"
                  | "pie chart"   | "pie graph"
                  | "scatter plot"
                  | "histogram"

chart_data_clause ::= "of" column_ref
                    | "comparing" column_ref "and" column_ref
                    | "of" column_ref "by" column_ref

title_clause    ::= "titled" STRING_LITERAL
                  | "with title" STRING_LITERAL
```

### Examples
```
Generate a bar chart of monthly revenue
Create a line chart comparing Q1 and Q2 sales
Plot a pie chart of revenue by region
Make a bar chart of total profit by product titled "Product Profitability"
```

---

## Pivot Statement

```ebnf
pivot_stmt      ::= pivot_kw "table" [ "by" column_ref { "and" column_ref } ]
                  | pivot_kw "table" "with" column_ref "as" pivot_role
                                    { "," column_ref "as" pivot_role }

pivot_kw        ::= "create" | "generate" | "make" | "build"

pivot_role      ::= "rows" | "columns" | "values"
```

### Examples
```
Create a pivot table by product and profit margin
Build a pivot table with region as rows, category as columns, revenue as values
```

---

## Sort Statement

```ebnf
sort_stmt       ::= sort_kw [ "by" column_ref ] [ sort_dir ]

sort_kw         ::= "sort" | "order" | "rank"

sort_dir        ::= "ascending"  | "asc"
                  | "descending" | "desc" | "highest first" | "lowest first"
```

### Examples
```
Sort by revenue descending
Order by profit ascending
Rank by total units highest first
```

---

## Terminals

```ebnf
IDENTIFIER      ::= LETTER { LETTER | DIGIT | "_" }

STRING_LITERAL  ::= '"' { any_char } '"'
                  | "'" { any_char } "'"

NUMBER          ::= DIGIT { DIGIT } [ "." DIGIT { DIGIT } ]

LETTER          ::= "a" .. "z" | "A" .. "Z"
DIGIT           ::= "0" .. "9"
```

---

## Synonym Mapping

RetailLang resolves synonyms before parsing. The following groups are treated
as equivalent:

| Canonical term | Accepted synonyms                        |
|----------------|------------------------------------------|
| `load`         | import, read, open                       |
| `compute`      | calculate, find, get, show               |
| `filter`       | where, only, select                      |
| `revenue`      | sales, income, turnover                  |
| `profit`       | earnings, margin, net                    |
| `units`        | quantity, qty, items, pieces             |
| `average`      | avg, mean                                |
| `total`        | sum                                      |
| `descending`   | desc, highest first                      |
| `ascending`    | asc, lowest first                        |

---

## Grammar Design Considerations

**Why EBNF over BNF?** The optional and repetition constructs in EBNF map
cleanly to Python list and optional parsing patterns used in the recursive
descent parser, making the grammar easier to implement directly.

**Why allow compound statements?** Retail analysts naturally chain operations
in a single sentence ("Load X and compute Y and generate a chart"). Supporting
compound statements with `and` / `,` allows the DSL to feel natural without
requiring users to write separate commands.

**Why keyword synonyms?** The target user is a non-technical business
stakeholder. Enforcing a single keyword like `compute` would break usability.
Synonyms are resolved in a pre-processing pass before tokenisation so the core
parser stays simple.

**Ambiguity management:** The grammar is intentionally LL(1)-friendly. Every
statement type begins with a distinct keyword group (`load_kw`, `compute_kw`,
`filter_kw`, etc.), allowing the parser to make single-token lookahead
decisions with no backtracking.