import pandas as pd


class PivotGenerator:
    """
    Builds pivot tables from a DataFrame using a PivotStatement AST node,
    and generates the equivalent Pandas code string.
    """

    AGG_MAP = {
        "sum":     "sum",
        "total":   "sum",
        "avg":     "mean",
        "average": "mean",
        "mean":    "mean",
        "count":   "count",
        "max":     "max",
        "min":     "min",
    }

    # ------------------------------------------------------------------
    # Live execution
    # ------------------------------------------------------------------

    def execute(self, df: pd.DataFrame, node: dict) -> pd.DataFrame:
        """
        Build and return a real pivot table DataFrame from a PivotStatement
        AST node and a loaded DataFrame.
        """
        index   = node.get("index",   self._infer_index(df))
        columns = node.get("columns", self._infer_columns(df, index))
        values  = node.get("values",  self._infer_values(df))
        aggfunc = self.AGG_MAP.get(node.get("aggfunc", "sum"), "sum")

        index   = index.lower()   if index   else index
        columns = columns.lower() if columns else columns
        values  = values.lower()  if values  else values

        df.columns = [c.lower().strip() for c in df.columns]

        pivot = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
            fill_value=0,
        )
        pivot.columns.name = None
        return pivot.reset_index()

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------

    def generate(self, node: dict) -> str:
        """Return a Pandas pivot_table code string from a PivotStatement node."""
        index   = node.get("index",   "row_col")
        columns = node.get("columns", "col_col")
        values  = node.get("values",  "value_col")
        aggfunc = self.AGG_MAP.get(node.get("aggfunc", "sum"), "sum")

        lines = [
            "import pandas as pd",
            "",
            "# Pivot table",
            "pivot = pd.pivot_table(",
            f'    df,',
            f'    index="{index}",',
            f'    columns="{columns}",',
            f'    values="{values}",',
            f'    aggfunc="{aggfunc}",',
            f'    fill_value=0,',
            ")",
            "pivot.columns.name = None",
            "pivot = pivot.reset_index()",
            "print(pivot)",
        ]
        return "\n".join(lines)

    def generate_styled(self, node: dict) -> str:
        """
        Return Pandas code that renders a styled pivot table
        with a heatmap highlight on numeric cells.
        """
        base = self.generate(node)
        style_lines = [
            "",
            "# Styled output (Jupyter / Streamlit)",
            "styled = pivot.style.background_gradient(",
            '    cmap="Blues",',
            "    subset=pivot.select_dtypes(include='number').columns,",
            ")",
        ]
        return base + "\n".join(style_lines)

    # ------------------------------------------------------------------
    # Inference helpers (used when AST node is partially specified)
    # ------------------------------------------------------------------

    def _infer_index(self, df: pd.DataFrame) -> str:
        """Pick the first categorical column as the row index."""
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        return cat_cols[0] if cat_cols else df.columns[0]

    def _infer_columns(self, df: pd.DataFrame, exclude: str) -> str:
        """Pick the second categorical column as the pivot column dimension."""
        cat_cols = [
            c for c in df.select_dtypes(exclude="number").columns
            if c.lower() != (exclude or "").lower()
        ]
        return cat_cols[0] if cat_cols else df.columns[1]

    def _infer_values(self, df: pd.DataFrame) -> str:
        """Pick the first numeric column as the values dimension."""
        num_cols = df.select_dtypes(include="number").columns.tolist()
        return num_cols[0] if num_cols else df.columns[-1]

    # ------------------------------------------------------------------
    # Summary helpers for the Streamlit UI
    # ------------------------------------------------------------------

    def summarize(self, pivot: pd.DataFrame) -> dict:
        """Return a dict of summary metrics for the pivot result."""
        numeric = pivot.select_dtypes(include="number")
        if numeric.empty:
            return {}
        return {
            "Rows":      len(pivot),
            "Columns":   len(numeric.columns),
            "Grand total": f"{numeric.values.sum():,.0f}",
            "Max cell":    f"{numeric.values.max():,.0f}",
        }