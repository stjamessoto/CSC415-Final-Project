from __future__ import annotations
from retaillang.lexer     import Token, TokenType
from retaillang.ast_nodes import (
    ProgramNode, LoadStatement, FilterStatement, ComputeStatement,
    ChartStatement, PivotStatement, SortStatement, Condition,
)
from retaillang.errors    import ParseError
from retaillang.synonyms  import resolve_keyword


# ------------------------------------------------------------------
# Aggregation + direction normalisation maps
# ------------------------------------------------------------------

AGG_CANONICAL = {
    "total":   "sum",
    "sum":     "sum",
    "average": "avg",
    "avg":     "avg",
    "mean":    "avg",
    "count":   "count",
    "max":     "max",
    "maximum": "max",
    "min":     "min",
    "minimum": "min",
    "number":  "count",
}

DIRECTION_CANONICAL = {
    "ascending":  "asc",
    "asc":        "asc",
    "descending": "desc",
    "desc":       "desc",
    "highest":    "desc",
    "lowest":     "asc",
}

CHART_TYPES = {
    "bar":       "bar",
    "line":      "line",
    "pie":       "pie",
    "scatter":   "scatter",
    "histogram": "histogram",
}


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens  = [t for t in tokens if t.type != TokenType.ARTICLE]
        self._pos     = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> ProgramNode:
        program = ProgramNode()
        while not self._at_end():
            self._skip_punct()
            if self._at_end():
                break
            stmt = self._parse_statement()
            if stmt:
                program.body.append(stmt)
        self._infer_chart_axes(program)
        return program

    def _infer_chart_axes(self, program: ProgramNode):
        """Backfill x/y on ChartStatements using the nearest preceding ComputeStatement."""
        last_compute = None
        for node in program.body:
            if isinstance(node, ComputeStatement):
                last_compute = node
            elif isinstance(node, ChartStatement) and last_compute:
                if not node.x and last_compute.group_by:
                    node.x = last_compute.group_by[0]
                if not node.y:
                    node.y = last_compute.column

    # ------------------------------------------------------------------
    # Statement dispatcher
    # ------------------------------------------------------------------

    def _parse_statement(self):
        tok = self._peek()

        if tok is None or tok.type == TokenType.EOF:
            return None

        val = tok.value.lower()

        if val == "load":
            return self._parse_load()
        elif val in ("filter", "where", "only"):
            return self._parse_filter()
        elif val in ("compute", "calculate", "find", "get", "show"):
            return self._parse_compute()
        elif val in ("generate", "create", "make", "plot",
                     "draw", "build"):
            return self._parse_chart_or_pivot()
        elif val in ("sort", "order", "rank"):
            return self._parse_sort()
        else:
            # skip unknown tokens rather than hard-crash
            self._advance()
            return None

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _parse_load(self) -> LoadStatement:
        self._expect_keyword("load")

        filename_tok = self._peek()
        if filename_tok is None or filename_tok.type != TokenType.FILENAME:
            raise ParseError(
                "Expected a filename after 'load' (e.g. sales.csv)",
                position=self._current_pos(),
            )
        filename = self._advance().value

        alias = None
        if self._peek_value() == "as":
            self._advance()
            alias_tok = self._advance()
            if alias_tok and alias_tok.type == TokenType.IDENTIFIER:
                alias = alias_tok.value

        return LoadStatement(filename=filename, alias=alias)

    # ------------------------------------------------------------------
    # Filter
    # ------------------------------------------------------------------

    def _parse_filter(self) -> FilterStatement:
        self._advance()  # consume filter/where/only

        # optional "by"
        if self._peek_value() == "by":
            self._advance()

        conditions = []
        bool_op    = "and"

        conditions.append(self._parse_condition())

        _STMT_STARTERS = {
            "compute", "calculate", "find", "get",
            "generate", "create", "make", "plot", "draw", "build",
            "sort", "order", "rank", "load", "import", "read",
        }
        while self._peek_value() in ("and", "or"):
            # peek past the conjunction — if a new statement starts, stop
            nxt_idx = self._pos + 1
            if nxt_idx < len(self._tokens):
                if self._tokens[nxt_idx].value.lower() in _STMT_STARTERS:
                    break
            bool_op = self._advance().value
            conditions.append(self._parse_condition())

        return FilterStatement(conditions=conditions, bool_op=bool_op)

    def _parse_condition(self) -> Condition:
        col_tok = self._peek()
        if col_tok is None or col_tok.type not in (
            TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.STRING
        ):
            raise ParseError(
                "Expected a column name in filter condition",
                position=self._current_pos(),
            )
        column = self._advance().value

        op_tok = self._peek()
        if op_tok is None or op_tok.type != TokenType.COMPARATOR:
            raise ParseError(
                f"Expected a comparator after column '{column}' "
                f"(e.g. =, >, <, >=, <=)",
                position=self._current_pos(),
            )
        operator = self._advance().value

        val_tok = self._peek()
        if val_tok is None or val_tok.type == TokenType.EOF:
            raise ParseError(
                f"Expected a value after '{column} {operator}'",
                position=self._current_pos(),
            )
        raw_val = self._advance().value

        # coerce numeric strings
        value: str | float = raw_val
        try:
            value = float(raw_val) if "." in raw_val else int(raw_val)
        except ValueError:
            pass

        return Condition(column=column, operator=operator, value=value)

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def _parse_compute(self) -> ComputeStatement:
        self._advance()  # consume compute / calculate / etc.

        # optional "of"
        if self._peek_value() == "of":
            self._advance()

        # aggregation function
        agg_tok = self._peek()
        if agg_tok is None:
            raise ParseError(
                "Expected an aggregation function after 'compute' "
                "(e.g. total, average, count)",
                position=self._current_pos(),
            )

        agg_raw  = agg_tok.value.lower()
        agg_func = AGG_CANONICAL.get(agg_raw)

        if agg_func:
            self._advance()
        else:
            agg_func = "sum"

        # optional "of"
        if self._peek_value() == "of":
            self._advance()

        # column name
        col_tok = self._peek()
        if col_tok is None or col_tok.type == TokenType.EOF:
            raise ParseError(
                "Expected a column name after aggregation function",
                position=self._current_pos(),
            )
        # skip filler words
        if col_tok.value.lower() in ("the", "a", "an"):
            self._advance()
            col_tok = self._peek()

        column = self._advance().value.lower()

        # group by clause
        group_by = []
        if self._peek_value() in ("by", "grouped", "per", "for"):
            self._advance()
            # optional "each"
            if self._peek_value() == "each":
                self._advance()

            while True:
                grp_tok = self._peek()
                if grp_tok is None or grp_tok.type in (
                    TokenType.EOF, TokenType.PUNCT
                ):
                    break
                if grp_tok.value.lower() in (
                    "and", "or", "generate", "create", "make",
                    "sort", "order", "filter", "where", "compute",
                    "then", "also"
                ):
                    break
                group_by.append(self._advance().value.lower())

                if self._peek_value() in (",", "and"):
                    nxt = self._tokens[self._pos + 1] \
                        if self._pos + 1 < len(self._tokens) else None
                    if nxt and nxt.value.lower() in (
                        "generate", "create", "sort", "filter",
                        "compute", "then"
                    ):
                        break
                    self._advance()

        return ComputeStatement(
            aggregation=agg_func,
            column=column,
            group_by=group_by,
        )

    # ------------------------------------------------------------------
    # Chart or Pivot dispatcher
    # ------------------------------------------------------------------

    def _parse_chart_or_pivot(self):
        self._advance()  # consume generate / create / make / etc.

        # peek ahead for "pivot"
        if self._peek_value() == "pivot":
            return self._parse_pivot_body()

        # peek ahead for chart type
        if self._peek_value() in CHART_TYPES:
            return self._parse_chart_body()

        # "a bar chart", "a line chart", "a pivot table"
        next_val = self._peek_value()
        if next_val in CHART_TYPES:
            return self._parse_chart_body()

        if next_val == "pivot":
            return self._parse_pivot_body()

        # fallback: try chart
        return self._parse_chart_body()

    # ------------------------------------------------------------------
    # Chart
    # ------------------------------------------------------------------

    def _parse_chart_body(self) -> ChartStatement:
        chart_type = "bar"
        title      = None
        compare    = []

        tok = self._peek()
        if tok and tok.value.lower() in CHART_TYPES:
            chart_type = CHART_TYPES[self._advance().value.lower()]

        # consume "chart" / "graph"
        if self._peek_value() in ("chart", "graph", "plot"):
            self._advance()

        # optional "of" / "comparing" / "titled"
        while not self._at_end() and self._peek_value() not in (
            "and", "filter", "sort", "compute", "load",
        ):
            val = self._peek_value()

            if val == "of":
                self._advance()

            elif val == "comparing":
                self._advance()
                compare.append(self._advance().value.lower()
                                if self._peek() else "")
                if self._peek_value() == "and":
                    self._advance()
                if self._peek() and self._peek().type in (
                    TokenType.IDENTIFIER, TokenType.KEYWORD
                ):
                    compare.append(self._advance().value.lower())

            elif val in ("titled", "title"):
                self._advance()
                if self._peek() and self._peek().type in (
                    TokenType.STRING, TokenType.IDENTIFIER
                ):
                    title = self._advance().value

            else:
                break

        return ChartStatement(
            chart_type=chart_type,
            title=title,
            compare=compare,
        )

    # ------------------------------------------------------------------
    # Pivot
    # ------------------------------------------------------------------

    def _parse_pivot_body(self) -> PivotStatement:
        # consume "pivot"
        if self._peek_value() == "pivot":
            self._advance()

        # consume "table"
        if self._peek_value() == "table":
            self._advance()

        index   = ""
        columns = ""
        values  = ""
        aggfunc = "sum"

        # style 1: "with region as rows, category as columns, revenue as values"
        if self._peek_value() == "with":
            self._advance()
            while not self._at_end():
                col_tok = self._peek()
                if col_tok is None or col_tok.type == TokenType.EOF:
                    break
                if col_tok.value.lower() in ("and", "generate", "sort"):
                    break

                col_name = self._advance().value.lower()

                if self._peek_value() != "as":
                    break
                self._advance()  # consume "as"

                role_tok = self._peek()
                if role_tok is None:
                    break
                role = self._advance().value.lower()

                if role in ("rows", "row", "index"):
                    index = col_name
                elif role in ("columns", "column", "cols"):
                    columns = col_name
                elif role in ("values", "value", "vals"):
                    values = col_name

                if self._peek_value() in (",", "and"):
                    nxt = self._tokens[self._pos + 1] \
                        if self._pos + 1 < len(self._tokens) else None
                    if nxt and nxt.value.lower() in (
                        "generate", "sort", "filter"
                    ):
                        break
                    self._advance()

        # style 2: "by product and region"
        elif self._peek_value() in ("by", "grouped"):
            self._advance()

            dims = []
            while not self._at_end():
                tok = self._peek()
                if tok is None or tok.type == TokenType.EOF:
                    break
                if tok.value.lower() in (
                    "generate", "sort", "filter", "compute"
                ):
                    break
                if tok.value.lower() in (",", "and"):
                    self._advance()
                    continue
                dims.append(self._advance().value.lower())

            if len(dims) >= 1:
                index = dims[0]
            if len(dims) >= 2:
                columns = dims[1]
            if len(dims) >= 3:
                values = dims[2]

        return PivotStatement(
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
        )

    # ------------------------------------------------------------------
    # Sort
    # ------------------------------------------------------------------

    def _parse_sort(self) -> SortStatement:
        self._advance()  # consume sort / order / rank

        # optional "by"
        if self._peek_value() == "by":
            self._advance()

        col_tok = self._peek()
        if col_tok is None or col_tok.type == TokenType.EOF:
            raise ParseError(
                "Expected a column name after 'sort by'",
                position=self._current_pos(),
            )
        column = self._advance().value.lower()

        direction = "desc"
        dir_tok   = self._peek()
        if dir_tok and dir_tok.value.lower() in DIRECTION_CANONICAL:
            direction = DIRECTION_CANONICAL[self._advance().value.lower()]
            # consume optional "first"
            if self._peek_value() == "first":
                self._advance()

        return SortStatement(column=column, direction=direction)

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _peek(self) -> Token | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _peek_value(self) -> str:
        tok = self._peek()
        return tok.value.lower() if tok else ""

    def _advance(self) -> Token:
        tok       = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _at_end(self) -> bool:
        tok = self._peek()
        return tok is None or tok.type == TokenType.EOF

    def _skip_punct(self):
        while not self._at_end() and self._peek_value() in (",", "and", "then", "also"):
            self._advance()

    def _expect_keyword(self, keyword: str) -> Token:
        tok = self._peek()
        if tok is None or tok.value.lower() != keyword:
            raise ParseError(
                f"Expected '{keyword}' but got "
                f"'{tok.value if tok else 'EOF'}'",
                position=self._current_pos(),
            )
        return self._advance()

    def _current_pos(self) -> int:
        tok = self._peek()
        return tok.position if tok else -1