import json
import pandas as pd
from datetime import datetime, timezone


class JSONGenerator:
    """
    Generates dashboard JSON specifications from a RetailLang AST.
    The output format is a self-contained dashboard spec that can be
    consumed by a front-end renderer or saved as a .json file.
    """

    DASHBOARD_VERSION = "1.0"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, ast: dict) -> str:
        """Return a dashboard JSON spec string from a parsed AST dict."""
        spec = self._build_spec(ast)
        return json.dumps(spec, indent=2)

    def generate_from_result(self, result: dict, command: str = "") -> str:
        """
        Build a dashboard JSON spec from a live execution result dict
        (as returned by PandasGenerator.execute).
        """
        spec = {
            "version":   self.DASHBOARD_VERSION,
            "generated": datetime.now(timezone.utc).isoformat(),
            "command":   command,
            "panels":    [],
        }

        output_type = result.get("output_type")

        if output_type == "dataframe":
            df = result.get("dataframe")
            if df is not None:
                spec["panels"].append(self._dataframe_panel(df))

        elif output_type == "chart":
            fig = result.get("figure")
            if fig:
                spec["panels"].append(self._chart_panel(fig))

        elif output_type == "pivot":
            df = result.get("dataframe")
            if df is not None:
                spec["panels"].append(self._pivot_panel(df))

        if result.get("metrics"):
            spec["panels"].insert(0, self._metrics_panel(result["metrics"]))

        if result.get("generated_code"):
            spec["generated_code"] = {
                "language": result.get("code_language", "python"),
                "source":   result["generated_code"],
            }

        return json.dumps(spec, indent=2)

    # ------------------------------------------------------------------
    # AST-driven spec builder
    # ------------------------------------------------------------------

    def _build_spec(self, ast: dict) -> dict:
        spec = {
            "version":   self.DASHBOARD_VERSION,
            "generated": datetime.now(timezone.utc).isoformat(),
            "panels":    [],
        }

        for node in ast.get("body", []):
            node_type = node.get("type")

            if node_type == "LoadStatement":
                spec["datasource"] = {
                    "type":     "file",
                    "filename": node["filename"],
                    "alias":    node.get("alias"),
                }

            elif node_type == "FilterStatement":
                spec["filters"] = [
                    {
                        "column":   c["column"],
                        "operator": c["operator"],
                        "value":    c["value"],
                    }
                    for c in node.get("conditions", [])
                ]

            elif node_type == "ComputeStatement":
                spec["panels"].append({
                    "type":        "table",
                    "title":       self._compute_title(node),
                    "aggregation": node.get("aggregation"),
                    "column":      node.get("column"),
                    "group_by":    node.get("group_by", []),
                })

            elif node_type == "ChartStatement":
                spec["panels"].append({
                    "type":       "chart",
                    "chart_type": node.get("chart_type", "bar"),
                    "title":      node.get("title", ""),
                    "x":          node.get("x", ""),
                    "y":          node.get("y", ""),
                })

            elif node_type == "PivotStatement":
                spec["panels"].append({
                    "type":    "pivot",
                    "title":   "Pivot table",
                    "index":   node.get("index"),
                    "columns": node.get("columns"),
                    "values":  node.get("values"),
                    "aggfunc": node.get("aggfunc", "sum"),
                })

            elif node_type == "SortStatement":
                spec["sort"] = {
                    "column":    node.get("column"),
                    "direction": node.get("direction", "desc"),
                }

        return spec

    # ------------------------------------------------------------------
    # Panel builders (used by generate_from_result)
    # ------------------------------------------------------------------

    def _dataframe_panel(self, df: pd.DataFrame) -> dict:
        return {
            "type":    "table",
            "title":   "Query result",
            "columns": list(df.columns),
            "rows":    df.head(100).to_dict(orient="records"),
            "total_rows": len(df),
        }

    def _chart_panel(self, fig) -> dict:
        try:
            return {
                "type":   "chart",
                "title":  fig.layout.title.text or "Chart",
                "plotly": json.loads(fig.to_json()),
            }
        except Exception:
            return {"type": "chart", "title": "Chart", "error": "Could not serialize figure"}

    def _pivot_panel(self, df: pd.DataFrame) -> dict:
        return {
            "type":    "pivot",
            "title":   "Pivot table",
            "columns": list(df.columns),
            "rows":    df.head(100).to_dict(orient="records"),
        }

    def _metrics_panel(self, metrics: dict) -> dict:
        return {
            "type":    "metrics",
            "title":   "Summary",
            "metrics": [
                {"label": k, "value": v}
                for k, v in metrics.items()
            ],
        }

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _compute_title(self, node: dict) -> str:
        agg    = node.get("aggregation", "total").title()
        col    = node.get("column", "").replace("_", " ").title()
        groups = node.get("group_by", [])
        if groups:
            by = ", ".join(g.replace("_", " ").title() for g in groups)
            return f"{agg} {col} by {by}"
        return f"{agg} {col}"

    def save(self, ast: dict, filepath: str):
        """Write the dashboard JSON spec to a file."""
        spec = self.generate(ast)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(spec)
        print(f"Dashboard spec saved to {filepath}")