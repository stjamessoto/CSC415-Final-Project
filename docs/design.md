# RetailLang — System Assumptions & Language Objectives

## 1. User Model

RetailLang is designed for **non-technical retail business stakeholders** —
analysts, managers, and executives who understand their data domain but have
no programming background. The target user can describe what they want in
plain English but cannot write Pandas, SQL, or Matplotlib code themselves.

### User assumptions

- The user knows their column names (e.g. `region`, `profit`, `category`)
- The user understands basic analytics concepts (averages, totals, charts)
- The user does not know Python syntax or SQL
- The user is working with tabular CSV or Excel data
- Commands are entered one at a time or chained with "and"

---

## 2. Intended Domain

RetailLang is scoped to **retail business analytics**. It is intentionally
narrow — this is a feature, not a limitation. A narrow scope allows the
grammar to be unambiguous and the synonym dictionary to be meaningful.

### Supported operations

| Operation       | Description                                      |
|-----------------|--------------------------------------------------|
| Load            | Read a CSV or Excel file into memory             |
| Compute         | Aggregate a numeric column (sum, avg, count)     |
| Filter          | Subset rows by a condition                       |
| Group by        | Aggregate across a categorical dimension         |
| Chart           | Generate a bar, line, or pie chart               |
| Pivot           | Build a pivot table across two dimensions        |
| Sort            | Order results by a column                        |

### Out of scope

The following operations are deliberately excluded from v0.1.0:

- Joining multiple datasets (no SQL-style JOIN)
- Machine learning or forecasting
- Real-time or streaming data
- Writing back to files or databases
- Multi-step branching or conditional logic (if/else)
- User-defined functions

---

## 3. Language Objectives

1. **Readability** — A RetailLang command should read like a sentence.
2. **Learnability** — A new user should write their first command in under
   60 seconds with no documentation.
3. **Predictability** — The same command always produces the same output.
4. **Transparency** — The system always shows the generated code so the user
   can learn from it.
5. **Forgiving input** — Synonyms, minor misspellings, and word order
   variation should not break parsing.

---

## 4. Design Trade-offs

### Trade-off 1: Expressiveness vs. simplicity

RetailLang sacrifices expressiveness for simplicity. A user cannot write
arbitrary expressions like `(revenue - cost) / revenue * 100`. This was a
deliberate choice — supporting arbitrary arithmetic would require a full
expression grammar that is significantly harder to parse and explain to
non-technical users. The trade-off is acceptable because the most common
retail KPIs (total revenue, average profit, count of orders) are all
first-class operations.

### Trade-off 2: Synonym resolution vs. grammar complexity

Synonyms are resolved in a pre-processing pass before tokenisation rather
than inside the grammar itself. This keeps the grammar clean and LL(1) but
means synonym resolution is a separate concern that must be maintained
independently. The benefit outweighs the cost — the parser stays simple and
testable.

### Trade-off 3: Single-file assumption

RetailLang v0.1.0 assumes one active dataset at a time. A `load` command
replaces the current dataset in memory. This avoids the complexity of a
symbol table and multi-dataset join logic at the cost of not supporting
cross-file analysis in a single command.

### Trade-off 4: Natural language parsing vs. formal grammar

A large language model could interpret completely free-form English.
RetailLang deliberately uses a formal grammar instead because:
- Output is deterministic and reproducible
- Errors are meaningful and actionable
- The system demonstrates compiler construction concepts
- No external API dependency is required

### Trade-off 5: Output format

RetailLang defaults to Pandas + Plotly output rather than raw SQL because
Pandas operates in-memory on CSV files without requiring a running database.
SQL output is also generated and shown in the "Generated code" tab, giving
users both options.

---

## 5. Error Handling Strategy

RetailLang uses a two-level error strategy:

**Level 1 — Lexer errors:** Unrecognised tokens trigger a `LexError` with
the offending token highlighted and a suggestion from the synonym dictionary
if a close match exists.

**Level 2 — Parser errors:** Structural errors (missing column name, unknown
file extension) trigger a `ParseError` with the position of the error and
a human-readable message.

Both error types surface a "Did you mean...?" suggestion where possible,
computed using edit distance against the known keyword and column vocabulary.

---

## 6. Limitations

- Column names must match the CSV header exactly (case-insensitive)
- File paths are relative to the working directory
- Charts support a maximum of two data dimensions
- Numeric formatting (currency symbols, percentages) is not parsed
- No support for date arithmetic (e.g. "last 30 days")
- Maximum recommended dataset size is ~500,000 rows (in-memory Pandas limit)