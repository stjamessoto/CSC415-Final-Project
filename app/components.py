import streamlit as st
import pandas as pd

def render_header():
    st.markdown("""
        <div style='padding: 1rem 0 0.5rem 0'>
            <h1 style='margin:0; font-size: 2rem;'>RetailLang IDE</h1>
            <p style='margin:0; opacity:0.6; font-size:0.95rem;'>
                Natural language → Pandas · SQL · Charts
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()


def render_command_input(default=""):
    st.subheader("Command")
    command = st.text_area(
        label="Enter a RetailLang command",
        value=default,
        height=100,
        placeholder='e.g. "Load sales.csv and compute total revenue by region"',
        label_visibility="collapsed",
    )
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        run = st.button("Run", type="primary", use_container_width=True)
    with col2:
        clear = st.button("Clear", use_container_width=True)
    return command, run, clear


def render_examples_sidebar():
    with st.sidebar:
        st.header("Example commands")
        examples = {
            "Revenue by region": "Load data/sales.csv and compute total revenue by region",
            "Bar chart": "Load data/sales.csv and compute total revenue by region and generate a bar chart",
            "Filter + compute": "Load data/orders.csv, filter by region = West, and compute total subtotal by channel",
            "Pivot table": "Load data/sales.csv and create a pivot table by product and region",
            "Line chart": "Load data/sales.csv and compute total revenue by region and generate a line chart",
            "Top products": "Load data/sales.csv and compute total revenue by product and sort by revenue descending",
            "Customer spend": "Load data/customers.csv and compute average total_spent by segment",
        }
        for label, cmd in examples.items():
            if st.button(label, use_container_width=True):
                st.session_state["selected_example"] = cmd
                st.rerun()

        st.divider()
        st.caption("RetailLang DSL · v0.1.0")


def render_output_tabs(result: dict):
    tabs = st.tabs(["Output", "Generated code", "AST", "Parse tree", "Tokens"])

    with tabs[0]:
        _render_output(result)

    with tabs[1]:
        _render_generated_code(result)

    with tabs[2]:
        _render_ast(result)

    with tabs[3]:
        _render_parse_tree(result)

    with tabs[4]:
        _render_token_breakdown(result)


def _render_output(result: dict):
    if result.get("error"):
        st.error(result["error"])
        if result.get("suggestion"):
            st.info(f"Did you mean: `{result['suggestion']}`?")
        return

    output_type = result.get("output_type")

    if output_type == "chart":
        fig = result.get("figure")
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="output_main_chart")

    elif output_type == "dataframe":
        df = result.get("dataframe")
        if df is not None:
            st.dataframe(df, use_container_width=True)

    elif output_type == "pivot":
        pivot = result.get("dataframe")
        if pivot is not None:
            st.dataframe(pivot, use_container_width=True)

    elif output_type == "sql":
        sql = result.get("sql")
        if sql:
            st.code(sql, language="sql")

    if result.get("summary"):
        st.caption(result["summary"])


def _render_generated_code(result: dict):
    if result.get("error"):
        st.warning("No code generated due to error.")
        return
    code = result.get("generated_code", "")
    lang = result.get("code_language", "python")
    if code:
        st.code(code, language=lang)
        st.download_button(
            label="Download code",
            data=code,
            file_name=f"retaillang_output.{'sql' if lang == 'sql' else 'py'}",
            mime="text/plain",
        )
    else:
        st.info("No generated code for this command.")


def _render_ast(result: dict):
    ast = result.get("ast")
    if ast:
        st.json(ast)
    else:
        st.info("No AST available.")


def _render_parse_tree(result: dict):
    tree = result.get("parse_tree")
    if tree:
        st.text(tree)
    else:
        st.info("No parse tree available.")


_TOKEN_COLORS = {
    "KEYWORD":    "#4c9be8",
    "IDENTIFIER": "#3dba71",
    "FILENAME":   "#f5a623",
    "STRING":     "#9b59b6",
    "NUMBER":     "#1abc9c",
    "COMPARATOR": "#e74c3c",
    "PUNCT":      "#95a5a6",
}


def _render_token_breakdown(result: dict):
    tokens = result.get("tokens")
    if not tokens:
        st.info("No token data available. Run a command first.")
        return

    visible = [t for t in tokens if t["type"] != "EOF"]

    # Colored chips
    chips = "<div style='display:flex;flex-wrap:wrap;gap:6px;margin-bottom:1rem;'>"
    for tok in visible:
        color = _TOKEN_COLORS.get(tok["type"], "#aaa")
        chips += (
            f"<span style='background:{color}22;border:1px solid {color};"
            f"border-radius:4px;padding:3px 8px;font-size:0.85rem;"
            f"color:{color};font-family:monospace;'>"
            f"<b>{tok['value']}</b>"
            f"<span style='opacity:0.7;font-size:0.72rem;margin-left:5px;'>"
            f"{tok['type']}</span></span>"
        )
    chips += "</div>"
    st.markdown("**Token stream**")
    st.markdown(chips, unsafe_allow_html=True)

    # Legend
    legend = "<div style='display:flex;flex-wrap:wrap;gap:10px;margin-bottom:1rem;'>"
    for ttype, color in _TOKEN_COLORS.items():
        legend += (
            f"<span style='display:flex;align-items:center;gap:4px;font-size:0.8rem;'>"
            f"<span style='width:10px;height:10px;border-radius:2px;"
            f"background:{color};display:inline-block;'></span>{ttype}</span>"
        )
    legend += "</div>"
    st.markdown("**Legend**")
    st.markdown(legend, unsafe_allow_html=True)

    # Detail table + type counts side by side
    if visible:
        df = pd.DataFrame(visible).rename(columns={"type": "Type", "value": "Value", "position": "Position"})
        counts = df["Type"].value_counts().reset_index().rename(columns={"index": "Type", "Type": "Count"})

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**All tokens**")
            st.dataframe(df, use_container_width=True, hide_index=True)
        with col2:
            st.markdown("**Type counts**")
            st.dataframe(counts, use_container_width=True, hide_index=True)


def render_error_banner(message: str, suggestion: str = None):
    st.error(message)
    if suggestion:
        st.info(f"Suggestion: {suggestion}")


def render_metrics(result: dict):
    if result.get("error") or not result.get("metrics"):
        return
    metrics = result["metrics"]
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)