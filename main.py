import argparse
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def get_version() -> str:
    return "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="retaillang",
        description=(
            "RetailLang — Natural language business analytics DSL.\n"
            "Translates plain English commands into Pandas, SQL, and charts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  retaillang run "Load sales.csv and compute total revenue by region"
  retaillang run "Load sales.csv and generate a bar chart" --output chart.html
  retaillang run examples/revenue_by_region.rl --file
  retaillang repl
  retaillang parse "Load sales.csv and compute total revenue by region"
  retaillang tokens "Load sales.csv and compute total revenue by region"
  retaillang sql "Load sales.csv and compute total revenue by region"
  retaillang validate examples/pivot_table.rl
  retaillang web
        """,
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"RetailLang {get_version()}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # --- run ---
    run_parser = subparsers.add_parser(
        "run",
        help="Execute a RetailLang command or .rl file",
    )
    run_parser.add_argument(
        "input",
        help="Command string or path to a .rl file",
    )
    run_parser.add_argument(
        "--file", "-f",
        action="store_true",
        help="Treat input as a path to a .rl file",
    )
    run_parser.add_argument(
        "--output", "-o",
        help="Save output to a file (.py, .sql, .json, .html)",
        default=None,
    )
    run_parser.add_argument(
        "--format",
        choices=["pandas", "sql", "json"],
        default="pandas",
        help="Output format (default: pandas)",
    )
    run_parser.add_argument(
        "--no-code",
        action="store_true",
        help="Suppress generated code output",
    )
    run_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors",
    )

    # --- repl ---
    subparsers.add_parser(
        "repl",
        help="Start the interactive RetailLang REPL",
    )

    # --- parse ---
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse a command and print the AST",
    )
    parse_parser.add_argument("input", help="Command string to parse")
    parse_parser.add_argument(
        "--format",
        choices=["json", "tree", "parse-tree"],
        default="tree",
        help="Output format: tree (AST), parse-tree (grammar rules), or json (default: tree)",
    )

    # --- tokens ---
    tokens_parser = subparsers.add_parser(
        "tokens",
        help="Tokenize a command and print the token stream",
    )
    tokens_parser.add_argument("input", help="Command string to tokenize")

    # --- sql ---
    sql_parser = subparsers.add_parser(
        "sql",
        help="Translate a command to SQL",
    )
    sql_parser.add_argument("input", help="Command string to translate")
    sql_parser.add_argument(
        "--output", "-o",
        help="Save SQL to a file",
        default=None,
    )

    # --- validate ---
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a .rl file without executing it",
    )
    validate_parser.add_argument("path", help="Path to a .rl file")

    # --- web ---
    web_parser = subparsers.add_parser(
        "web",
        help="Launch the RetailLang Streamlit web IDE",
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the web IDE on (default: 8501)",
    )
    web_parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable login wall for local development",
    )

    return parser


# ------------------------------------------------------------------
# Pipeline helpers
# ------------------------------------------------------------------

def compile_command(command: str) -> tuple:
    """
    Run the full lexer → parser pipeline.
    Returns (tokens, ast) or raises on error.
    """
    from retaillang.lexer  import Lexer
    from retaillang.parser import Parser

    lexer  = Lexer(command)
    tokens = lexer.tokenize()
    ast    = Parser(tokens).parse()
    return tokens, ast, lexer


def execute_command(command: str) -> dict:
    """
    Run the full compiler + executor pipeline.
    Returns the result dict.
    """
    from retaillang.executor import Executor

    tokens, ast, lexer = compile_command(command)
    result = Executor().execute(ast)
    result["parse_tree"] = lexer.format_token_stream()
    result["ast"]        = ast.to_dict() if hasattr(ast, "to_dict") else {}
    return result


def load_rl_file(path: str) -> list[str]:
    """
    Read a .rl file and return a list of non-empty, non-comment commands.
    Handles multi-line commands joined by trailing commas or 'and'.
    """
    file_path = Path(path)
    if not file_path.exists():
        print(f"Error: file not found — {path}", file=sys.stderr)
        sys.exit(1)
    if file_path.suffix != ".rl":
        print(f"Warning: expected a .rl file, got {file_path.suffix}")

    raw_lines = file_path.read_text(encoding="utf-8").splitlines()

    commands  = []
    buffer    = []

    for line in raw_lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            if buffer:
                commands.append(" ".join(buffer))
                buffer = []
            continue

        buffer.append(stripped)

        last_word = stripped.rstrip(",").strip().lower().split()[-1]
        continues = stripped.endswith(",") or last_word == "and"

        if not continues:
            commands.append(" ".join(buffer))
            buffer = []

    if buffer:
        commands.append(" ".join(buffer))

    return [c for c in commands if c.strip()]


def print_result(result: dict, show_code: bool = True, quiet: bool = False):
    """Pretty-print an execution result to stdout."""
    if result.get("error"):
        print(f"\nError: {result['error']}", file=sys.stderr)
        if result.get("suggestion"):
            print(f"Did you mean: '{result['suggestion']}'?", file=sys.stderr)
        return

    if quiet:
        return

    output_type = result.get("output_type")

    if output_type == "dataframe":
        df = result.get("dataframe")
        if df is not None:
            print("\nResult:")
            print(df.to_string(index=False))
            if result.get("summary"):
                print(f"\n{result['summary']}")

    elif output_type == "pivot":
        df = result.get("dataframe")
        if df is not None:
            print("\nPivot table:")
            print(df.to_string(index=False))

    elif output_type == "chart":
        print("\nChart generated successfully.")
        print("Use --output chart.html to save the chart to a file.")

    elif output_type == "sql":
        sql = result.get("sql", "")
        if sql:
            print(f"\nSQL:\n{sql}")

    if result.get("metrics"):
        print("\nMetrics:")
        for label, value in result["metrics"].items():
            print(f"  {label}: {value}")

    if show_code and result.get("generated_code"):
        print(f"\nGenerated code ({result.get('code_language', 'python')}):")
        print("-" * 40)
        print(result["generated_code"])
        print("-" * 40)


def save_output(result: dict, path: str):
    """Save execution output to a file based on extension."""
    ext = Path(path).suffix.lower()

    if ext == ".py":
        code = result.get("generated_code", "")
        Path(path).write_text(code, encoding="utf-8")
        print(f"Python code saved to {path}")

    elif ext == ".sql":
        from generators.sql_gen import SQLGenerator
        sql = SQLGenerator().generate(result.get("ast", {}))
        Path(path).write_text(sql, encoding="utf-8")
        print(f"SQL saved to {path}")

    elif ext == ".json":
        from generators.json_gen import JSONGenerator
        spec = JSONGenerator().generate_from_result(result)
        Path(path).write_text(spec, encoding="utf-8")
        print(f"Dashboard JSON saved to {path}")

    elif ext == ".html":
        fig = result.get("figure")
        if fig:
            fig.write_html(path)
            print(f"Chart saved to {path}")
        else:
            print("No chart to save. Run a chart command first.")

    else:
        print(f"Unsupported output format: {ext}", file=sys.stderr)


# ------------------------------------------------------------------
# Subcommand handlers
# ------------------------------------------------------------------

def handle_run(args):
    command_input = args.input

    if args.file or command_input.endswith(".rl"):
        commands = load_rl_file(command_input)
        if not commands:
            print("No commands found in file.")
            return

        print(f"Running {len(commands)} command(s) from {command_input}\n")
        errors = 0

        for i, cmd in enumerate(commands, 1):
            print(f"[{i}/{len(commands)}] {cmd}")
            try:
                result = execute_command(cmd)
                print_result(
                    result,
                    show_code=not args.no_code,
                    quiet=args.quiet,
                )
                if result.get("error"):
                    errors += 1
            except Exception as e:
                print(f"  Error: {e}", file=sys.stderr)
                errors += 1
            print()

        if errors:
            print(f"\n{errors} command(s) failed.", file=sys.stderr)
            sys.exit(1)

    else:
        try:
            result = execute_command(command_input)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        print_result(
            result,
            show_code=not args.no_code,
            quiet=args.quiet,
        )

        if args.output:
            save_output(result, args.output)

        if result.get("error"):
            sys.exit(1)


def handle_repl(args):
    print(f"RetailLang REPL v{get_version()}")
    print("Type a command and press Enter to execute.")
    print("Commands: exit, quit, help, clear, examples\n")

    history = []

    while True:
        try:
            raw = input("retaillang> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not raw:
            continue

        if raw.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        if raw.lower() == "help":
            print("\nRetailLang REPL commands:")
            print("  exit / quit     Exit the REPL")
            print("  help            Show this message")
            print("  clear           Clear the screen")
            print("  examples        Show example commands")
            print("  history         Show command history")
            print("  run <file.rl>   Execute a .rl file\n")
            continue

        if raw.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue

        if raw.lower() == "examples":
            print("\nExample commands:")
            print('  Load sales.csv and compute total revenue by region')
            print('  Load sales.csv and generate a bar chart')
            print('  Load orders.csv, filter by status = Completed, and compute total total by channel')
            print('  Load customers.csv and create a pivot table by segment and loyalty_tier')
            print('  Load sales.csv and compute total profit by product and sort by profit descending\n')
            continue

        if raw.lower() == "history":
            if not history:
                print("No history yet.")
            else:
                for i, cmd in enumerate(history, 1):
                    print(f"  {i}. {cmd}")
            print()
            continue

        if raw.lower().startswith("run "):
            path = raw[4:].strip()
            commands = load_rl_file(path)
            for cmd in commands:
                print(f"  > {cmd}")
                try:
                    result = execute_command(cmd)
                    print_result(result, show_code=True)
                except Exception as e:
                    print(f"  Error: {e}", file=sys.stderr)
            continue

        history.append(raw)

        try:
            result = execute_command(raw)
            print_result(result, show_code=True)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

        print()


def handle_parse(args):
    try:
        _, ast, _ = compile_command(args.input)
    except Exception as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    ast_dict = ast.to_dict() if hasattr(ast, "to_dict") else {}

    if args.format == "json":
        print(json.dumps(ast_dict, indent=2))
    elif args.format == "parse-tree":
        _print_parse_tree(ast_dict)
    else:
        _print_ast_tree(ast_dict)


def handle_tokens(args):
    try:
        from retaillang.lexer import Lexer
        lexer  = Lexer(args.input)
        tokens = lexer.tokenize()
        print(f"\nToken stream for: {args.input!r}\n")
        print(lexer.format_token_stream())
    except Exception as e:
        print(f"Lex error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_sql(args):
    try:
        _, ast, _ = compile_command(args.input)
        from generators.sql_gen import SQLGenerator
        sql = SQLGenerator().generate(
            ast.to_dict() if hasattr(ast, "to_dict") else {}
        )
        print(f"\nSQL output:\n{'-' * 40}\n{sql}\n{'-' * 40}")
        if args.output:
            Path(args.output).write_text(sql, encoding="utf-8")
            print(f"SQL saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_validate(args):
    commands = load_rl_file(args.path)
    print(f"Validating {args.path} — {len(commands)} command(s) found\n")

    errors   = 0
    warnings = 0

    for i, cmd in enumerate(commands, 1):
        try:
            _, ast, _ = compile_command(cmd)
            ast_dict  = ast.to_dict() if hasattr(ast, "to_dict") else {}
            node_types = [n["type"] for n in ast_dict.get("body", [])]

            has_load  = "LoadStatement" in node_types
            has_chart = "ChartStatement" in node_types
            has_compute = "ComputeStatement" in node_types

            if has_chart and not has_compute:
                print(f"  [{i}] Warning: chart without compute — x/y axes may be inferred")
                warnings += 1
            elif not has_load:
                print(f"  [{i}] Warning: no Load statement — file must already be loaded")
                warnings += 1
            else:
                print(f"  [{i}] OK — {' → '.join(node_types)}")

        except Exception as e:
            print(f"  [{i}] Error: {e}")
            errors += 1

    print(f"\n{len(commands)} checked · {errors} error(s) · {warnings} warning(s)")

    if errors:
        sys.exit(1)


def handle_web(args):
    import subprocess

    app_path = Path(__file__).parent / "app" / "app.py"
    if not app_path.exists():
        print(f"Error: app/app.py not found at {app_path}", file=sys.stderr)
        sys.exit(1)

    env = os.environ.copy()
    if args.no_auth:
        env["RETAILLANG_NO_AUTH"] = "1"

    print(f"Starting RetailLang web IDE on http://localhost:{args.port}")
    print("Press Ctrl+C to stop.\n")

    try:
        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run",
                str(app_path),
                f"--server.port={args.port}",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--browser.gatherUsageStats=false",
            ],
            env=env,
            check=True,
        )
    except KeyboardInterrupt:
        print("\nWeb IDE stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting web IDE: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Streamlit not found. Install it with: pip install streamlit",
            file=sys.stderr,
        )
        sys.exit(1)


# ------------------------------------------------------------------
# AST tree printer
# ------------------------------------------------------------------

def _print_ast_tree(ast: dict, indent: int = 0):
    prefix = "  " * indent
    node_type = ast.get("type", "Unknown")
    print(f"{prefix}{node_type}")

    skip = {"type", "body"}
    for key, val in ast.items():
        if key in skip:
            continue
        if isinstance(val, list) and val and isinstance(val[0], dict):
            print(f"{prefix}  {key}:")
            for item in val:
                _print_ast_tree(item, indent + 2)
        elif isinstance(val, dict):
            print(f"{prefix}  {key}:")
            _print_ast_tree(val, indent + 2)
        elif val is not None:
            print(f"{prefix}  {key}: {val}")

    for child in ast.get("body", []):
        _print_ast_tree(child, indent + 1)


# ------------------------------------------------------------------
# Concrete parse tree printer
# ------------------------------------------------------------------

def _ast_node_to_parse_tree(node: dict) -> dict:
    """Convert a single AST node dict into a parse-tree dict (with grammar rule labels)."""
    t = node.get("type", "")

    if t == "Program":
        children = [_ast_node_to_parse_tree(n) for n in node.get("body", [])]
        if len(children) > 1:
            return {"label": "program", "children": [
                {"label": "compound_stmt", "children": children}
            ]}
        return {"label": "program", "children": children}

    if t == "LoadStatement":
        kids = [
            {"label": "load_kw",  "value": "load"},
            {"label": "FILENAME", "value": node["filename"]},
        ]
        if node.get("alias"):
            kids += [
                {"label": "\"as\""},
                {"label": "IDENTIFIER", "value": node["alias"]},
            ]
        return {"label": "load_stmt", "children": kids}

    if t == "FilterStatement":
        kids = [{"label": "filter_kw", "value": "filter"}]
        for i, cond in enumerate(node.get("conditions", [])):
            if i > 0:
                kids.append({"label": "bool_op", "value": node.get("bool_op", "and")})
            kids.append({"label": "condition", "children": [
                {"label": "column_ref", "value": cond["column"]},
                {"label": "comparator",  "value": cond["operator"]},
                {"label": "value",       "value": str(cond["value"])},
            ]})
        return {"label": "filter_stmt", "children": kids}

    if t == "ComputeStatement":
        metric = {"label": "metric_expr", "children": [
            {"label": "agg_func",   "value": node["aggregation"]},
            {"label": "column_ref", "value": node["column"]},
        ]}
        kids = [{"label": "compute_kw", "value": "compute"}, metric]
        if node.get("group_by"):
            grp = [{"label": "group_kw", "value": "by"}]
            for col in node["group_by"]:
                grp.append({"label": "column_ref", "value": col})
            kids.append({"label": "group_clause", "children": grp})
        return {"label": "compute_stmt", "children": kids}

    if t == "ChartStatement":
        kids = [
            {"label": "chart_kw",   "value": "generate"},
            {"label": "chart_type", "value": f"{node['chart_type']} chart"},
        ]
        if node.get("x") or node.get("y"):
            kids.append({"label": "chart_data_clause", "children": [
                {"label": "column_ref", "value": node.get("x", "")},
                {"label": "column_ref", "value": node.get("y", "")},
            ]})
        if node.get("title"):
            kids.append({"label": "title_clause", "value": f'"{node["title"]}"'})
        return {"label": "chart_stmt", "children": kids}

    if t == "PivotStatement":
        kids = [
            {"label": "pivot_kw", "value": "create"},
            {"label": "\"table\""},
        ]
        if node.get("index"):
            kids.append({"label": "pivot_role", "value": f'{node["index"]} as rows'})
        if node.get("columns"):
            kids.append({"label": "pivot_role", "value": f'{node["columns"]} as columns'})
        if node.get("values"):
            kids.append({"label": "pivot_role", "value": f'{node["values"]} as values'})
        return {"label": "pivot_stmt", "children": kids}

    if t == "SortStatement":
        return {"label": "sort_stmt", "children": [
            {"label": "sort_kw",    "value": "sort"},
            {"label": "\"by\""},
            {"label": "column_ref", "value": node["column"]},
            {"label": "sort_dir",   "value": node["direction"]},
        ]}

    return {"label": t}


def _render_parse_tree_node(node: dict, prefix: str, is_last: bool):
    connector = "+-- " if is_last else "|-- "
    child_pfx = prefix + ("    " if is_last else "|   ")
    label     = node.get("label", "?")
    value     = node.get("value")

    if value is not None:
        print(f"{prefix}{connector}{label:<18} {value!r}")
    else:
        print(f"{prefix}{connector}{label}")

    children = node.get("children", [])
    for i, child in enumerate(children):
        _render_parse_tree_node(child, child_pfx, i == len(children) - 1)


def _print_parse_tree(ast_dict: dict):
    """Print the concrete parse tree showing grammar rule names."""
    tree     = _ast_node_to_parse_tree(ast_dict)
    print(tree.get("label", "program"))
    children = tree.get("children", [])
    for i, child in enumerate(children):
        _render_parse_tree_node(child, "", i == len(children) - 1)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    handlers = {
        "run":      handle_run,
        "repl":     handle_repl,
        "parse":    handle_parse,
        "tokens":   handle_tokens,
        "sql":      handle_sql,
        "validate": handle_validate,
        "web":      handle_web,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()