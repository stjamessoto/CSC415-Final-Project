import streamlit as st

from generators.chart_gen import build_bar_chart


def render_live_preview(result: dict):
    """
    Renders a live chart preview inside a Streamlit container.
    Called by app.py after every successful execution.
    """
    if not result or result.get("error"):
        return

    output_type = result.get("output_type")

    with st.container():
        if output_type == "chart":
            fig = result.get("figure")
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="preview_main_chart")

        elif output_type in ("dataframe", "pivot"):
            df = result.get("dataframe")
            if df is not None:
                st.dataframe(df, use_container_width=True)

                if not df.empty:
                    numeric_cols = df.select_dtypes(include="number").columns.tolist()
                    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

                    if numeric_cols and cat_cols:
                        st.caption("Quick chart from result")
                        fig = build_bar_chart(
                            df,
                            x=cat_cols[0],
                            y=numeric_cols[0],
                            title="Result preview",
                        )
                        st.plotly_chart(fig, use_container_width=True, key="preview_quick_chart")
