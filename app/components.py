import streamlit as st

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
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        run = st.button("Run", type="primary", use_container_width=True)
    with col2:
        clear = st.button("Clear", use_container_width=True)
    return command, run, clear


def render_examples_sidebar():
    with st.sidebar:
        st.header("Example commands")
        examples = {
            "Revenue by region": "Load sales.csv and compute total revenue by region",
            "Monthly bar chart": "Load sales.csv and generate a bar chart of monthly revenue",
            "Filter + compute": "Load orders.csv, filter by region = West, and compute total profit",
            "Pivot table": "Load sales.csv and create a pivot table by product and profit margin",
            "Q1 vs Q2 chart": "Load sales.csv and generate a bar chart comparing Q1 and Q2 revenue",
            "Top products": "Load products.csv and compute total units sold by product, sort descending",
            "Customer revenue": "Load customers.csv and compute average revenue by customer segment",
        }
        for label, cmd in examples.items():
            if st.button(label, use_container_width=True):
                st.session_state["selected_example"] = cmd
                st.rerun()

        st.divider()
        st.caption("RetailLang DSL · v0.1.0")


def render_output_tabs(result: dict):
    tabs = st.tabs(["Output", "Generated code", "AST", "Parse tree"])

    with tabs[0]:
        _render_output(result)

    with tabs[1]:
        _render_generated_code(result)

    with tabs[2]:
        _render_ast(result)

    with tabs[3]:
        _render_parse_tree(result)


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
            st.plotly_chart(fig, use_container_width=True)

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