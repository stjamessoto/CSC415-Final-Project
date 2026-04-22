import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retaillang.lexer  import Lexer
from retaillang.parser import Parser


def parse(command: str) -> dict:
    """Helper: lex + parse a command and return the AST dict."""
    tokens = Lexer(command).tokenize()
    ast    = Parser(tokens).parse()
    return ast.to_dict()


class TestProgramNode:
    """Verify the root ProgramNode is always produced."""

    def test_program_node_type(self):
        ast = parse("Load sales.csv")
        assert ast["type"] == "Program"

    def test_program_has_body(self):
        ast = parse("Load sales.csv")
        assert "body" in ast
        assert isinstance(ast["body"], list)

    def test_empty_body_on_empty_input(self):
        tokens = Lexer("").tokenize()
        ast    = Parser(tokens).parse().to_dict()
        assert ast["body"] == []


class TestLoadStatement:
    """Verify LoadStatement parsing."""

    def test_basic_load(self):
        ast  = parse("Load sales.csv")
        node = ast["body"][0]
        assert node["type"]     == "LoadStatement"
        assert node["filename"] == "sales.csv"
        assert node["alias"]    is None

    def test_load_with_alias(self):
        ast  = parse("Load orders.csv as orders")
        node = ast["body"][0]
        assert node["alias"] == "orders"

    def test_load_xlsx(self):
        ast  = parse("Load products.xlsx")
        node = ast["body"][0]
        assert node["filename"] == "products.xlsx"

    def test_load_synonym_import(self):
        ast  = parse("import sales.csv")
        node = ast["body"][0]
        assert node["type"] == "LoadStatement"

    def test_load_synonym_read(self):
        ast  = parse("read customers.csv")
        node = ast["body"][0]
        assert node["type"] == "LoadStatement"


class TestFilterStatement:
    """Verify FilterStatement parsing."""

    def test_basic_filter_equals(self):
        ast  = parse("Load sales.csv filter by region = West")
        node = next(n for n in ast["body"] if n["type"] == "FilterStatement")
        assert node["conditions"][0]["column"]   == "region"
        assert node["conditions"][0]["operator"] == "="
        assert node["conditions"][0]["value"]    == "West"

    def test_filter_greater_than(self):
        ast  = parse("Load sales.csv filter by profit > 1000")
        node = next(n for n in ast["body"] if n["type"] == "FilterStatement")
        assert node["conditions"][0]["operator"] == ">"
        assert node["conditions"][0]["value"]    == "1000"

    def test_filter_greater_equal(self):
        ast  = parse("Load sales.csv filter by profit >= 500")
        node = next(n for n in ast["body"] if n["type"] == "FilterStatement")
        assert node["conditions"][0]["operator"] == ">="

    def test_filter_multiple_conditions_and(self):
        ast  = parse("Load sales.csv filter by region = West and profit > 500")
        node = next(n for n in ast["body"] if n["type"] == "FilterStatement")
        assert len(node["conditions"]) == 2
        assert node["bool_op"]         == "and"

    def test_filter_synonym_where(self):
        ast  = parse("Load sales.csv where region = East")
        node = next(n for n in ast["body"] if n["type"] == "FilterStatement")
        assert node["conditions"][0]["column"] == "region"

    def test_filter_string_value_preserved(self):
        ast  = parse("Load sales.csv filter by category = Electronics")
        node = next(n for n in ast["body"] if n["type"] == "FilterStatement")
        assert node["conditions"][0]["value"] == "Electronics"


class TestComputeStatement:
    """Verify ComputeStatement parsing."""

    def test_basic_compute_total(self):
        ast  = parse("Load sales.csv compute total revenue by region")
        node = next(n for n in ast["body"] if n["type"] == "ComputeStatement")
        assert node["aggregation"] == "sum"
        assert node["column"]      == "revenue"
        assert "region"            in node["group_by"]

    def test_compute_average(self):
        ast  = parse("Load sales.csv compute average profit by product")
        node = next(n for n in ast["body"] if n["type"] == "ComputeStatement")
        assert node["aggregation"] in ("avg", "average", "mean")

    def test_compute_count(self):
        ast  = parse("Load orders.csv compute count of orders by region")
        node = next(n for n in ast["body"] if n["type"] == "ComputeStatement")
        assert node["aggregation"] == "count"

    def test_compute_no_group_by(self):
        ast  = parse("Load sales.csv compute total revenue")
        node = next(n for n in ast["body"] if n["type"] == "ComputeStatement")
        assert node["group_by"] == []

    def test_compute_multiple_group_by(self):
        ast  = parse("Load sales.csv compute total revenue by region and product")
        node = next(n for n in ast["body"] if n["type"] == "ComputeStatement")
        assert len(node["group_by"]) == 2

    def test_compute_synonym_calculate(self):
        ast  = parse("Load sales.csv calculate total revenue by region")
        node = next(n for n in ast["body"] if n["type"] == "ComputeStatement")
        assert node["type"] == "ComputeStatement"


class TestChartStatement:
    """Verify ChartStatement parsing."""

    def test_bar_chart(self):
        ast  = parse("Load sales.csv generate a bar chart")
        node = next(n for n in ast["body"] if n["type"] == "ChartStatement")
        assert node["chart_type"] == "bar"

    def test_line_chart(self):
        ast  = parse("Load sales.csv generate a line chart")
        node = next(n for n in ast["body"] if n["type"] == "ChartStatement")
        assert node["chart_type"] == "line"

    def test_pie_chart(self):
        ast  = parse("Load sales.csv create a pie chart")
        node = next(n for n in ast["body"] if n["type"] == "ChartStatement")
        assert node["chart_type"] == "pie"

    def test_chart_with_title(self):
        ast  = parse('Load sales.csv generate a bar chart titled "Revenue Report"')
        node = next(n for n in ast["body"] if n["type"] == "ChartStatement")
        assert node["title"] == "Revenue Report"

    def test_chart_x_y_inferred_from_compute(self):
        ast  = parse(
            "Load sales.csv compute total revenue by region "
            "and generate a bar chart"
        )
        chart_node = next(n for n in ast["body"] if n["type"] == "ChartStatement")
        assert chart_node["x"] == "region"
        assert chart_node["y"] in ("revenue", "sum_revenue", "total_revenue")


class TestPivotStatement:
    """Verify PivotStatement parsing."""

    def test_basic_pivot(self):
        ast  = parse("Load sales.csv create a pivot table by product and region")
        node = next(n for n in ast["body"] if n["type"] == "PivotStatement")
        assert node["type"]  == "PivotStatement"
        assert node["index"] == "product"

    def test_pivot_with_roles(self):
        ast  = parse(
            "Load sales.csv build a pivot table with "
            "region as rows, category as columns, revenue as values"
        )
        node = next(n for n in ast["body"] if n["type"] == "PivotStatement")
        assert node["index"]   == "region"
        assert node["columns"] == "category"
        assert node["values"]  == "revenue"


class TestSortStatement:
    """Verify SortStatement parsing."""

    def test_sort_descending(self):
        ast  = parse("Load sales.csv sort by revenue descending")
        node = next(n for n in ast["body"] if n["type"] == "SortStatement")
        assert node["column"]    == "revenue"
        assert node["direction"] == "desc"

    def test_sort_ascending(self):
        ast  = parse("Load sales.csv sort by profit ascending")
        node = next(n for n in ast["body"] if n["type"] == "SortStatement")
        assert node["direction"] == "asc"

    def test_sort_default_descending(self):
        ast  = parse("Load sales.csv sort by revenue")
        node = next(n for n in ast["body"] if n["type"] == "SortStatement")
        assert node["direction"] == "desc"


class TestCompoundStatements:
    """Verify chaining multiple statements with 'and' or ','."""

    def test_load_and_compute(self):
        ast   = parse("Load sales.csv and compute total revenue by region")
        types = [n["type"] for n in ast["body"]]
        assert "LoadStatement"    in types
        assert "ComputeStatement" in types

    def test_load_filter_compute_chart(self):
        ast = parse(
            "Load sales.csv, filter by region = West, "
            "compute total revenue by product, and generate a bar chart"
        )
        types = [n["type"] for n in ast["body"]]
        assert "LoadStatement"    in types
        assert "FilterStatement"  in types
        assert "ComputeStatement" in types
        assert "ChartStatement"   in types

    def test_statement_order_preserved(self):
        ast   = parse("Load sales.csv and compute total revenue by region")
        types = [n["type"] for n in ast["body"]]
        assert types.index("LoadStatement") < types.index("ComputeStatement")

    def test_three_statements(self):
        ast = parse(
            "Load orders.csv, filter by profit > 100, "
            "and compute total revenue by product"
        )
        assert len(ast["body"]) == 3


class TestParserErrors:
    """Verify the parser raises meaningful errors on bad input."""

    def test_missing_filename_raises(self):
        from retaillang.errors import ParseError
        with pytest.raises(ParseError):
            parse("Load")

    def test_filter_without_column_raises(self):
        from retaillang.errors import ParseError
        with pytest.raises(ParseError):
            parse("Load sales.csv filter by")

    def test_filter_without_value_raises(self):
        from retaillang.errors import ParseError
        with pytest.raises(ParseError):
            parse("Load sales.csv filter by region =")

    def test_compute_without_column_raises(self):
        from retaillang.errors import ParseError
        with pytest.raises(ParseError):
            parse("Load sales.csv compute total")

    def test_unknown_statement_raises(self):
        from retaillang.errors import ParseError
        with pytest.raises((ParseError, Exception)):
            parse("Load sales.csv UNKNOWNVERB something")