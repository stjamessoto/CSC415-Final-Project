import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.components import (
    render_header,
    render_command_input,
    render_examples_sidebar,
    render_output_tabs,
    render_metrics,
)
from app.auth import login_wall, logout
from app.preview import render_live_preview

st.set_page_config(
    page_title="RetailLang IDE",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


def run_command(command: str) -> dict:
    """
    Pipe the command through the RetailLang compiler pipeline.
    Returns a result dict consumed by the UI components.
    """
    try:
        from retaillang.lexer    import Lexer
        from retaillang.parser   import Parser
        from retaillang.executor import Executor

        lexer    = Lexer(command)
        tokens   = lexer.tokenize()
        parser   = Parser(tokens)
        ast      = parser.parse()
        executor = Executor()
        result   = executor.execute(ast)
        result["parse_tree"] = lexer.format_token_stream()
        result["ast"]        = ast.to_dict() if hasattr(ast, "to_dict") else str(ast)
        return result

    except SyntaxError as e:
        return {"error": str(e), "suggestion": getattr(e, "suggestion", None)}
    except FileNotFoundError as e:
        return {"error": f"File not found: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def main():
    username = login_wall()

    render_examples_sidebar()

    with st.sidebar:
        st.divider()
        st.write(f"Signed in as **{username}**")
        if st.button("Sign out", use_container_width=True):
            logout()

    render_header()

    if "selected_example" in st.session_state:
        default_command = st.session_state.pop("selected_example")
    else:
        default_command = st.session_state.get("last_command", "")

    command, run_clicked, clear_clicked = render_command_input(default=default_command)

    if clear_clicked:
        st.session_state["last_command"] = ""
        st.rerun()

    if run_clicked and command.strip():
        st.session_state["last_command"] = command

        with st.spinner("Parsing and executing..."):
            result = run_command(command)

        st.session_state["last_result"] = result

    result = st.session_state.get("last_result")

    if result:
        render_metrics(result)
        st.divider()

        col_left, col_right = st.columns([1, 1])

        with col_left:
            render_output_tabs(result)

        with col_right:
            st.subheader("Live preview")
            render_live_preview(result)

    elif not run_clicked:
        st.info("Enter a RetailLang command above and click Run to see results.")


if __name__ == "__main__":
    main()