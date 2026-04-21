import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str = None,
) -> go.Figure:
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        title_font_size=16,
        margin=dict(t=50, b=40, l=40, r=20),
        xaxis_title=x.replace("_", " ").title(),
        yaxis_title=y.replace("_", " ").title(),
    )
    return fig


def build_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str = None,
) -> go.Figure:
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        template="plotly_white",
        markers=True,
    )
    fig.update_layout(
        title_font_size=16,
        margin=dict(t=50, b=40, l=40, r=20),
    )
    return fig


def build_pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str = "",
) -> go.Figure:
    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        title_font_size=16,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def build_pivot_display(df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    return pd.pivot_table(
        df,
        index=index,
        columns=columns,
        values=values,
        aggfunc="sum",
        fill_value=0,
    )


def chart_from_df(df: pd.DataFrame, chart_type: str, x: str, y: str, title: str = "") -> go.Figure:
    """Dispatch helper: builds a chart figure from a dataframe."""
    builders = {
        "bar":  build_bar_chart,
        "line": build_line_chart,
        "pie":  build_pie_chart,
    }
    builder = builders.get(chart_type, build_bar_chart)

    if chart_type == "pie":
        return builder(df, names=x, values=y, title=title)
    return builder(df, x=x, y=y, title=title)


class ChartGenerator:
    """
    Wraps the chart builder functions for use by PandasGenerator.execute().
    Accepts a ChartStatement AST node and a loaded DataFrame.
    """

    def execute(self, df: pd.DataFrame, node: dict) -> go.Figure:
        chart_type = node.get("chart_type", "bar")
        x     = node.get("x", "")
        y     = node.get("y", "")
        title = node.get("title", f"{y} by {x}".replace("_", " ").title())

        df.columns = [c.lower().strip() for c in df.columns]
        x = x.lower()
        y = y.lower()

        return chart_from_df(df, chart_type, x, y, title)

    def generate(self, node: dict) -> str:
        """Return a Plotly Express code string from a ChartStatement node."""
        chart_type = node.get("chart_type", "bar")
        x     = node.get("x", "")
        y     = node.get("y", "")
        title = node.get("title", f"{y} by {x}".replace("_", " ").title())

        lines = ["import plotly.express as px", ""]
        if chart_type == "bar":
            lines.append(f'fig = px.bar(df, x="{x}", y="{y}", title="{title}", template="plotly_white")')
        elif chart_type == "line":
            lines.append(f'fig = px.line(df, x="{x}", y="{y}", title="{title}", template="plotly_white", markers=True)')
        elif chart_type == "pie":
            lines.append(f'fig = px.pie(df, names="{x}", values="{y}", title="{title}", template="plotly_white")')
        lines.append("fig.show()")
        return "\n".join(lines)
