class SQLGenerator:
    """
    Walks a RetailLang AST and emits a SQL SELECT statement as a string.
    Targets ANSI SQL compatible with SQLite, PostgreSQL, and MySQL.
    """

    AGG_MAP = {
        "sum":     "SUM",
        "total":   "SUM",
        "avg":     "AVG",
        "average": "AVG",
        "mean":    "AVG",
        "count":   "COUNT",
        "max":     "MAX",
        "maximum": "MAX",
        "min":     "MIN",
        "minimum": "MIN",
    }

    OP_MAP = {
        "=":            "=",
        "==":           "=",
        "is":           "=",
        "!=":           "!=",
        "is not":       "!=",
        ">":            ">",
        "greater than": ">",
        "<":            "<",
        "less than":    "<",
        ">=":           ">=",
        "at least":     ">=",
        "<=":           "<=",
        "at most":      "<=",
    }

    def generate(self, ast: dict) -> str:
        """Return a SQL query string from a parsed AST dict."""
        table      = None
        filters    = []
        bool_op    = "AND"
        select_col = "*"
        agg_func   = None
        group_by   = []
        order_by   = None
        direction  = "DESC"

        for node in ast.get("body", []):
            node_type = node.get("type")

            if node_type == "LoadStatement":
                filename = node["filename"]
                table    = filename.rsplit(".", 1)[0]

            elif node_type == "FilterStatement":
                bool_op = "AND" if node.get("bool_op", "and") == "and" else "OR"
                for cond in node.get("conditions", []):
                    col     = cond["column"]
                    op      = self.OP_MAP.get(cond["operator"], "=")
                    val     = cond["value"]
                    val_str = f"'{val}'" if isinstance(val, str) and \
                        not str(val).replace(".", "").isnumeric() else str(val)
                    filters.append(f"{col} {op} {val_str}")

            elif node_type == "ComputeStatement":
                agg_func   = self.AGG_MAP.get(node["aggregation"], "SUM")
                select_col = node["column"]
                group_by   = node.get("group_by", [])

            elif node_type == "SortStatement":
                order_by  = node["column"]
                direction = "ASC" if node.get("direction") == "asc" else "DESC"

        if not table:
            return "-- Error: no table loaded"

        return self._build_query(
            table, select_col, agg_func,
            filters, bool_op, group_by,
            order_by, direction,
        )

    # ------------------------------------------------------------------
    # Query builder
    # ------------------------------------------------------------------

    def _build_query(
        self,
        table:      str,
        col:        str,
        agg_func:   str | None,
        filters:    list[str],
        bool_op:    str,
        group_by:   list[str],
        order_by:   str | None,
        direction:  str,
    ) -> str:
        lines = []

        # SELECT clause
        if agg_func and group_by:
            group_cols = ",\n    ".join(group_by)
            agg_alias  = f"{agg_func.lower()}_{col}"
            lines.append("SELECT")
            lines.append(f"    {group_cols},")
            lines.append(f"    {agg_func}({col}) AS {agg_alias}")
        elif agg_func:
            lines.append("SELECT")
            lines.append(f"    {agg_func}({col}) AS {agg_func.lower()}_{col}")
        else:
            lines.append("SELECT")
            lines.append(f"    {col}")

        # FROM clause
        lines.append(f"FROM {table}")

        # WHERE clause
        if filters:
            joiner = f"\n    {bool_op} "
            lines.append(f"WHERE {joiner.join(filters)}")

        # GROUP BY clause
        if group_by:
            lines.append(f"GROUP BY {', '.join(group_by)}")

        # ORDER BY clause
        if order_by:
            lines.append(f"ORDER BY {order_by} {direction}")
        elif agg_func and group_by:
            agg_alias = f"{agg_func.lower()}_{col}"
            lines.append(f"ORDER BY {agg_alias} {direction}")

        lines.append(";")
        return "\n".join(lines)

    def generate_create_table(self, filename: str, columns: list[dict]) -> str:
        """
        Bonus helper: generate a CREATE TABLE statement from a list of
        column dicts with 'name' and 'dtype' keys.
        """
        table = filename.rsplit(".", 1)[0]
        type_map = {
            "int64":   "INTEGER",
            "float64": "REAL",
            "object":  "TEXT",
            "bool":    "INTEGER",
        }
        col_defs = []
        for c in columns:
            sql_type = type_map.get(str(c.get("dtype")), "TEXT")
            col_defs.append(f"    {c['name']} {sql_type}")
        col_str = ",\n".join(col_defs)
        return f"CREATE TABLE IF NOT EXISTS {table} (\n{col_str}\n);"

    def generate_insert(self, filename: str, rows: list[dict]) -> str:
        """
        Bonus helper: generate INSERT statements for a list of row dicts.
        """
        if not rows:
            return ""
        table   = filename.rsplit(".", 1)[0]
        cols    = ", ".join(rows[0].keys())
        inserts = []
        for row in rows:
            vals = ", ".join(
                f"'{v}'" if isinstance(v, str) else str(v)
                for v in row.values()
            )
            inserts.append(f"INSERT INTO {table} ({cols}) VALUES ({vals});")
        return "\n".join(inserts)