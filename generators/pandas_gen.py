import pandas as pd
from typing import Any


class PandasGenerator:
    """
    Walks a RetailLang AST and emits executable Pandas Python code
    as a string, plus optionally executes it and returns a live DataFrame.
    """

    AGG_MAP = {
        "sum":   "sum",
        "total": "sum",
        "avg":   "mean",
        "average": "mean",
        "mean":  "mean",
        "count": "count",
        "max":   "max",
        "maximum": "max",
        "min":   "min",
        "minimum": "min",
    }

    OP_MAP = {
        "=":          "==",
        "==":         "==",
        "is":         "==",
        "!=":         "!=",
        "is not":     "!=",
        ">":          ">",
        "greater than": ">",
        "<":          "<",
        "less than":  "<",
        ">=":         ">=",
        "at least":   ">=",
        "<=":         "<=",
        "at most":    "<=",
    }

    def __init__(self):
        self._lines: list[str] = []
        self._indent: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, ast: dict) -> str:
        """Return a Pandas Python script as a string from a parsed AST dict."""
        self._lines = []
        self._indent = 0
        self._emit("import pandas as pd")
        self._emit("import plotly.express as px")
        self._emit("")

        for node in ast.get("body", []):
            self._dispatch(node)
            self._emit("")

        return "\n".join(self._lines)

    def execute(self, ast: dict) -> dict:
        """
        Execute the AST against real data using live Pandas operations.
        Returns a result dict containing the DataFrame, summary, and
        generated code string.
        """
        result = {
            "output_type":     None,
            "dataframe":       None,
            "generated_code":  self.generate(ast),
            "code_language":   "python",
            "summary":         None,
            "metrics":         {},
            "error":           None,
        }

        df: pd.DataFrame | None = None

        for node in ast.get("body", []):
            node_type = node.get("type")

            if node_type == "LoadStatement":
                df = self._exec_load(node)

            elif node_type == "FilterStatement":
                if df is None:
                    result["error"] = "Filter called before Load."
                    return result
                df = self._exec_filter(df, node)

            elif node_type == "ComputeStatement":
                if df is None:
                    result["error"] = "Compute called before Load."
                    return result
                df = self._exec_compute(df, node)
                result["output_type"] = "dataframe"
                result["dataframe"]   = df
                result["summary"]     = self._compute_summary(df, node)
                result["metrics"]     = self._compute_metrics(df, node)

            elif node_type == "SortStatement":
                if df is None:
                    result["error"] = "Sort called before Load."
                    return result
                df = self._exec_sort(df, node)
                result["dataframe"] = df

            elif node_type == "ChartStatement":
                if df is None:
                    result["error"] = "Chart called before Load."
                    return result
                from generators.chart_gen import ChartGenerator
                chart_gen = ChartGenerator()
                fig = chart_gen.execute(df, node)
                result["output_type"] = "chart"
                result["figure"]      = fig

            elif node_type == "PivotStatement":
                if df is None:
                    result["error"] = "Pivot called before Load."
                    return result
                from generators.pivot_gen import PivotGenerator
                pivot_gen = PivotGenerator()
                pivot_df  = pivot_gen.execute(df, node)
                result["output_type"] = "pivot"
                result["dataframe"]   = pivot_df

        return result

    # ------------------------------------------------------------------
    # Code generation helpers
    # ------------------------------------------------------------------

    def _dispatch(self, node: dict):
        node_type = node.get("type")
        dispatch = {
            "LoadStatement":    self._gen_load,
            "FilterStatement":  self._gen_filter,
            "ComputeStatement": self._gen_compute,
            "SortStatement":    self._gen_sort,
            "ChartStatement":   self._gen_chart,
            "PivotStatement":   self._gen_pivot,
        }
        handler = dispatch.get(node_type)
        if handler:
            handler(node)

    def _gen_load(self, node: dict):
        filename = node["filename"]
        alias    = node.get("alias") or "df"
        ext      = filename.rsplit(".", 1)[-1].lower()
        readers  = {
            "csv":     f'pd.read_csv("{filename}")',
            "xlsx":    f'pd.read_excel("{filename}")',
            "json":    f'pd.read_json("{filename}")',
            "parquet": f'pd.read_parquet("{filename}")',
        }
        reader = readers.get(ext, f'pd.read_csv("{filename}")')
        self._emit(f"# Load")
        self._emit(f"{alias} = {reader}")

    def _gen_filter(self, node: dict):
        self._emit("# Filter")
        conditions = node.get("conditions", [])
        bool_op    = node.get("bool_op", "and")
        parts = []
        for cond in conditions:
            col = cond["column"]
            op  = self.OP_MAP.get(cond["operator"], "==")
            val = cond["value"]
            val_str = f'"{val}"' if isinstance(val, str) else str(val)
            parts.append(f'(df["{col}"] {op} {val_str})')
        joiner = " & " if bool_op == "and" else " | "
        mask   = joiner.join(parts)
        self._emit(f"df = df[{mask}]")

    def _gen_compute(self, node: dict):
        agg      = self.AGG_MAP.get(node["aggregation"], "sum")
        col      = node["column"]
        group_by = node.get("group_by", [])
        self._emit("# Compute")
        if group_by:
            groups = ", ".join(f'"{g}"' for g in group_by)
            self._emit(f'result = df.groupby([{groups}])["{col}"].{agg}().reset_index()')
            col_alias = f"{agg}_{col}"
            self._emit(f'result.columns = [{groups}, "{col_alias}"]')
            self._emit("df = result")
        else:
            self._emit(f'result = df["{col}"].{agg}()')
            self._emit(f'print(f"{agg.title()} of {col}: {{result}}")')

    def _gen_sort(self, node: dict):
        col       = node["column"]
        direction = node.get("direction", "desc")
        ascending = "True" if direction == "asc" else "False"
        self._emit("# Sort")
        self._emit(f'df = df.sort_values("{col}", ascending={ascending})')

    def _gen_chart(self, node: dict):
        chart_type = node.get("chart_type", "bar")
        x     = node.get("x", "")
        y     = node.get("y", "")
        title = node.get("title", f"{y} by {x}".title())
        self._emit("# Chart")
        if chart_type == "bar":
            self._emit(f'fig = px.bar(df, x="{x}", y="{y}", title="{title}", template="plotly_white")')
        elif chart_type == "line":
            self._emit(f'fig = px.line(df, x="{x}", y="{y}", title="{title}", template="plotly_white", markers=True)')
        elif chart_type == "pie":
            self._emit(f'fig = px.pie(df, names="{x}", values="{y}", title="{title}", template="plotly_white")')
        self._emit("fig.show()")

    def _gen_pivot(self, node: dict):
        index   = node.get("index", "")
        columns = node.get("columns", "")
        values  = node.get("values", "")
        aggfunc = node.get("aggfunc", "sum")
        self._emit("# Pivot")
        self._emit(
            f'pivot = pd.pivot_table(df, index="{index}", columns="{columns}", '
            f'values="{values}", aggfunc="{aggfunc}", fill_value=0)'
        )
        self._emit("print(pivot)")

    # ------------------------------------------------------------------
    # Live execution helpers
    # ------------------------------------------------------------------

    def _exec_load(self, node: dict) -> pd.DataFrame:
        filename = node["filename"]
        ext      = filename.rsplit(".", 1)[-1].lower()
        readers  = {
            "csv":     pd.read_csv,
            "xlsx":    pd.read_excel,
            "json":    pd.read_json,
            "parquet": pd.read_parquet,
        }
        reader = readers.get(ext, pd.read_csv)
        df = reader(filename)
        df.columns = [c.lower().strip() for c in df.columns]
        return df

    def _exec_filter(self, df: pd.DataFrame, node: dict) -> pd.DataFrame:
        conditions = node.get("conditions", [])
        bool_op    = node.get("bool_op", "and")
        mask = None
        for cond in conditions:
            col = cond["column"].lower()
            op  = self.OP_MAP.get(cond["operator"], "==")
            val = cond["value"]
            if isinstance(val, str) and not val.replace(".", "").isnumeric():
                cond_mask = df[col].astype(str).str.lower() == val.lower() \
                    if op == "==" else self._apply_op(df[col].astype(str), op, val.lower())
            else:
                val = float(val) if "." in str(val) else int(val) \
                    if str(val).isnumeric() else val
                cond_mask = self._apply_op(df[col], op, val)
            mask = cond_mask if mask is None else (
                mask & cond_mask if bool_op == "and" else mask | cond_mask
            )
        return df[mask] if mask is not None else df

    def _apply_op(self, series: Any, op: str, val: Any) -> Any:
        ops = {
            "==": lambda s, v: s == v,
            "!=": lambda s, v: s != v,
            ">":  lambda s, v: s > v,
            "<":  lambda s, v: s < v,
            ">=": lambda s, v: s >= v,
            "<=": lambda s, v: s <= v,
        }
        return ops.get(op, lambda s, v: s == v)(series, val)

    def _exec_compute(self, df: pd.DataFrame, node: dict) -> pd.DataFrame:
        agg      = self.AGG_MAP.get(node["aggregation"], "sum")
        col      = node["column"].lower()
        group_by = [g.lower() for g in node.get("group_by", [])]
        if group_by:
            result = df.groupby(group_by)[col].agg(agg).reset_index()
            result.columns = group_by + [f"{agg}_{col}"]
            return result
        val = df[col].agg(agg)
        return pd.DataFrame({col: [val]})

    def _exec_sort(self, df: pd.DataFrame, node: dict) -> pd.DataFrame:
        col       = node["column"].lower()
        direction = node.get("direction", "desc")
        # After compute, columns are renamed (e.g. revenue → sum_revenue); fall back to partial match
        if col not in df.columns:
            matches = [c for c in df.columns if col in c.lower()]
            if matches:
                col = matches[0]
        return df.sort_values(col, ascending=(direction == "asc"))

    # ------------------------------------------------------------------
    # Metrics + summary
    # ------------------------------------------------------------------

    def _compute_summary(self, df: pd.DataFrame, node: dict) -> str:
        agg = self.AGG_MAP.get(node["aggregation"], "sum")
        col = node["column"]
        rows = len(df)
        return f"{rows} rows · {agg}({col})"

    def _compute_metrics(self, df: pd.DataFrame, node: dict) -> dict:
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            return {}
        metrics = {}
        for col in list(numeric.columns)[:3]:
            total = numeric[col].sum()
            metrics[col.replace("_", " ").title()] = (
                f"{total:,.0f}" if total > 100 else f"{total:,.2f}"
            )
        return metrics

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _emit(self, line: str = ""):
        self._lines.append("    " * self._indent + line)