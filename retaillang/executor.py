from __future__ import annotations
import pandas as pd

from retaillang.ast_nodes import (
    ProgramNode, LoadStatement, FilterStatement, ComputeStatement,
    ChartStatement, PivotStatement, SortStatement,
)
from retaillang.errors    import ExecutionError, FileLoadError, ColumnNotFoundError
from retaillang.synonyms  import resolve_column, suggest_column


class Executor:
    """
    Walks a RetailLang ProgramNode AST and executes each statement
    against a live Pandas DataFrame, returning a result dict consumed
    by the CLI and Streamlit IDE.
    """

    AGG_MAP = {
        "sum":   "sum",
        "avg":   "mean",
        "count": "count",
        "max":   "max",
        "min":   "min",
    }

    OP_MAP = {
        "=":   "==",
        "==":  "==",
        "!=":  "!=",
        ">":   ">",
        "<":   "<",
        ">=":  ">=",
        "<=":  "<=",
    }

    def __init__(self):
        self._df:      pd.DataFrame | None = None
        self._columns: list[str]           = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, ast: ProgramNode) -> dict:
        result = {
            "output_type":    None,
            "dataframe":      None,
            "figure":         None,
            "generated_code": "",
            "code_language":  "python",
            "summary":        None,
            "metrics":        {},
            "parse_tree":     None,
            "ast":            ast.to_dict(),
            "error":          None,
            "suggestion":     None,
        }

        self._df      = None
        self._columns = []

        try:
            self._generate_code(ast, result)

            for node in ast.body:
                self._dispatch(node, result)

        except FileLoadError as e:
            result["error"]      = str(e)
            result["suggestion"] = e.suggestion
        except ColumnNotFoundError as e:
            result["error"]      = str(e)
            result["suggestion"] = e.suggestion
        except ExecutionError as e:
            result["error"]      = str(e)
            result["suggestion"] = e.suggestion
        except FileNotFoundError as e:
            result["error"] = f"File not found: {e}"
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"

        return result

    # ------------------------------------------------------------------
    # Statement dispatcher
    # ------------------------------------------------------------------

    def _dispatch(self, node, result: dict):
        handlers = {
            LoadStatement:    self._exec_load,
            FilterStatement:  self._exec_filter,
            ComputeStatement: self._exec_compute,
            ChartStatement:   self._exec_chart,
            PivotStatement:   self._exec_pivot,
            SortStatement:    self._exec_sort,
        }
        handler = handlers.get(type(node))
        if handler:
            handler(node, result)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _exec_load(self, node: LoadStatement, result: dict):
        filename = node.filename
        ext      = filename.rsplit(".", 1)[-1].lower()

        readers = {
            "csv":     pd.read_csv,
            "xlsx":    pd.read_excel,
            "xls":     pd.read_excel,
            "json":    pd.read_json,
            "parquet": pd.read_parquet,
        }

        reader = readers.get(ext)
        if not reader:
            raise FileLoadError(f"Unsupported file type: .{ext}")

        try:
            df = reader(filename)
        except FileNotFoundError:
            data_path = f"data/{filename}"
            try:
                df = reader(data_path)
                filename = data_path
            except FileNotFoundError:
                raise FileLoadError(f"File not found: '{filename}'")
        except Exception as e:
            raise FileLoadError(f"Could not load '{filename}': {e}")

        df.columns    = [c.lower().strip() for c in df.columns]
        self._df      = df
        self._columns = list(df.columns)

        result["output_type"] = "dataframe"
        result["dataframe"]   = df
        result["summary"]     = (
            f"Loaded {filename} — {len(df):,} rows × {len(df.columns)} columns"
        )

    # ------------------------------------------------------------------
    # Filter
    # ------------------------------------------------------------------

    def _exec_filter(self, node: FilterStatement, result: dict):
        self._require_df("filter")
        df      = self._df
        bool_op = node.bool_op
        mask    = None

        for cond in node.conditions:
            col = self._resolve_col(cond.column)
            op  = self.OP_MAP.get(cond.operator, "==")
            val = cond.value

            if df[col].dtype == object:
                series    = df[col].astype(str).str.lower()
                val_str   = str(val).lower()
                cond_mask = self._apply_op(series, op, val_str)
            else:
                try:
                    val_num   = float(val)
                    cond_mask = self._apply_op(df[col], op, val_num)
                except (ValueError, TypeError):
                    cond_mask = self._apply_op(df[col], op, val)

            if mask is None:
                mask = cond_mask
            elif bool_op == "and":
                mask = mask & cond_mask
            else:
                mask = mask | cond_mask

        self._df      = df[mask] if mask is not None else df
        self._columns = list(self._df.columns)
        result["dataframe"] = self._df
        result["summary"]   = f"Filtered to {len(self._df):,} rows"

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def _exec_compute(self, node: ComputeStatement, result: dict):
        self._require_df("compute")
        df       = self._df
        agg      = self.AGG_MAP.get(node.aggregation, "sum")
        col      = self._resolve_col(node.column)
        group_by = [self._resolve_col(g) for g in node.group_by]

        if group_by:
            computed = df.groupby(group_by)[col].agg(agg).reset_index()
            col_alias = f"{agg}_{col}"
            computed.columns = group_by + [col_alias]
        else:
            val      = df[col].agg(agg)
            computed = pd.DataFrame({col: [val]})
            col_alias = col

        self._df              = computed
        self._columns         = list(self._df.columns)
        result["output_type"] = "dataframe"
        result["dataframe"]   = computed
        result["summary"]     = self._make_summary(agg, col, group_by, computed)
        result["metrics"]     = self._make_metrics(computed)

    # ------------------------------------------------------------------
    # Chart
    # ------------------------------------------------------------------

    def _exec_chart(self, node: ChartStatement, result: dict):
        self._require_df("generate a chart")
        df = self._df

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols     = df.select_dtypes(exclude="number").columns.tolist()

        x = node.x or (cat_cols[0]     if cat_cols     else df.columns[0])
        y = node.y or (numeric_cols[0]  if numeric_cols else df.columns[-1])

        try:
            x = self._resolve_col(x)
        except Exception:
            x = cat_cols[0] if cat_cols else df.columns[0]
        try:
            y = self._resolve_col(y)
        except Exception:
            y = numeric_cols[0] if numeric_cols else df.columns[-1]

        title = node.title or f"{y.replace('_', ' ').title()} by {x.replace('_', ' ').title()}"

        from generators.chart_gen import ChartGenerator
        chart_node_dict = {
            "type":       "ChartStatement",
            "chart_type": node.chart_type,
            "x":          x,
            "y":          y,
            "title":      title,
        }
        fig = ChartGenerator().execute(df, chart_node_dict)

        result["output_type"] = "chart"
        result["figure"]      = fig
        result["summary"]     = f"{node.chart_type.title()} chart: {y} by {x}"

    # ------------------------------------------------------------------
    # Pivot
    # ------------------------------------------------------------------

    def _exec_pivot(self, node: PivotStatement, result: dict):
        self._require_df("create a pivot table")
        df = self._df

        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        num_cols = df.select_dtypes(include="number").columns.tolist()

        index   = self._resolve_col(node.index)   if node.index   else (cat_cols[0] if cat_cols else df.columns[0])
        columns = self._resolve_col(node.columns) if node.columns else (cat_cols[1] if len(cat_cols) > 1 else cat_cols[0])
        values  = self._resolve_col(node.values)  if node.values  else (num_cols[0] if num_cols else df.columns[-1])
        aggfunc = self.AGG_MAP.get(node.aggfunc, "sum")

        pivot = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
            fill_value=0,
        )
        pivot.columns.name = None
        pivot = pivot.reset_index()

        result["output_type"] = "pivot"
        result["dataframe"]   = pivot
        result["summary"]     = (
            f"Pivot: {values} ({aggfunc}) — "
            f"{index} × {columns} — "
            f"{pivot.shape[0]} rows × {pivot.shape[1]} cols"
        )

    # ------------------------------------------------------------------
    # Sort
    # ------------------------------------------------------------------

    def _exec_sort(self, node: SortStatement, result: dict):
        self._require_df("sort")
        col       = self._resolve_col(node.column)
        ascending = node.direction == "asc"
        self._df      = self._df.sort_values(col, ascending=ascending)
        self._columns = list(self._df.columns)
        result["dataframe"] = self._df
        result["summary"]   = (
            f"Sorted by {col} "
            f"({'ascending' if ascending else 'descending'})"
        )

    # ------------------------------------------------------------------
    # Code generation pass
    # ------------------------------------------------------------------

    def _generate_code(self, ast: ProgramNode, result: dict):
        from generators.pandas_gen import PandasGenerator
        result["generated_code"] = PandasGenerator().generate(ast.to_dict())
        result["code_language"]  = "python"

    # ------------------------------------------------------------------
    # Column resolution
    # ------------------------------------------------------------------

    def _resolve_col(self, name: str) -> str:
        """
        Resolve a column name against the loaded DataFrame columns.
        Tries exact match, then synonym resolution, then fuzzy match.
        Raises ColumnNotFoundError with a suggestion if nothing matches.
        """
        lower = name.lower()

        if lower in self._columns:
            return lower

        canonical = resolve_column(lower)
        if canonical in self._columns:
            return canonical

        for col in self._columns:
            if lower in col or col in lower:
                return col

        suggestion = suggest_column(lower, self._columns)
        raise ColumnNotFoundError(name, self._columns)

    # ------------------------------------------------------------------
    # Operator application
    # ------------------------------------------------------------------

    def _apply_op(self, series, op: str, val):
        ops = {
            "==": lambda s, v: s == v,
            "!=": lambda s, v: s != v,
            ">":  lambda s, v: s > v,
            "<":  lambda s, v: s < v,
            ">=": lambda s, v: s >= v,
            "<=": lambda s, v: s <= v,
        }
        return ops.get(op, lambda s, v: s == v)(series, val)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_df(self, operation: str):
        if self._df is None:
            raise ExecutionError(
                f"Cannot '{operation}' — no dataset loaded. "
                f"Add a 'Load <file>.csv' statement first."
            )

    def _make_summary(
        self,
        agg: str,
        col: str,
        group_by: list[str],
        df: pd.DataFrame,
    ) -> str:
        label = {
            "sum":   "Total",
            "mean":  "Average",
            "count": "Count",
            "max":   "Max",
            "min":   "Min",
        }.get(agg, agg.title())

        if group_by:
            by = ", ".join(group_by)
            return f"{label} {col} by {by} — {len(df)} groups"
        return f"{label} {col}"

    def _make_metrics(self, df: pd.DataFrame) -> dict:
        metrics  = {}
        num_cols = df.select_dtypes(include="number").columns.tolist()
        for col in num_cols[:3]:
            total = df[col].sum()
            metrics[col.replace("_", " ").title()] = (
                f"{total:,.0f}" if total > 100 else f"{total:,.2f}"
            )
        return metrics