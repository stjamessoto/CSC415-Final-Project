import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generators.pandas_gen import PandasGenerator
from generators.sql_gen    import SQLGenerator
from generators.pivot_gen  import PivotGenerator
from generators.json_gen   import JSONGenerator


# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "region":  ["West", "West", "East", "East", "North"],
        "product": ["Laptop", "Phone", "Laptop", "Tablet", "Phone"],
        "revenue": [1200.0, 800.0, 950.0, 600.0, 700.0],
        "profit":  [300.0, 150.0, 200.0, 100.0, 120.0],
        "units":   [10, 20, 15, 8, 12],
    })


@pytest.fixture
def load_ast():
    return {
        "type": "Program",
        "body": [
            {"type": "LoadStatement", "filename": "sales.csv", "alias": None}
        ],
    }


@pytest.fixture
def compute_ast():
    return {
        "type": "Program",
        "body": [
            {"type": "LoadStatement",    "filename": "sales.csv", "alias": None},
            {"type": "ComputeStatement", "aggregation": "sum",
             "column": "revenue",       "group_by": ["region"]},
        ],
    }


@pytest.fixture
def filter_ast():
    return {
        "type": "Program",
        "body": [
            {"type": "LoadStatement",   "filename": "sales.csv", "alias": None},
            {"type": "FilterStatement", "bool_op": "and",
             "conditions": [{"column": "region", "operator": "=", "value": "West"}]},
        ],
    }


@pytest.fixture
def chart_ast():
    return {
        "type": "Program",
        "body": [
            {"type": "LoadStatement",    "filename": "sales.csv", "alias": None},
            {"type": "ComputeStatement", "aggregation": "sum",
             "column": "revenue",        "group_by": ["region"]},
            {"type": "ChartStatement",   "chart_type": "bar",
             "x": "region",              "y": "revenue", "title": "Revenue by region"},
        ],
    }


@pytest.fixture
def pivot_ast():
    return {
        "type": "Program",
        "body": [
            {"type": "LoadStatement",  "filename": "sales.csv", "alias": None},
            {"type": "PivotStatement", "index": "product",
             "columns": "region",      "values": "revenue", "aggfunc": "sum"},
        ],
    }


@pytest.fixture
def sort_ast():
    return {
        "type": "Program",
        "body": [
            {"type": "LoadStatement",    "filename": "sales.csv", "alias": None},
            {"type": "ComputeStatement", "aggregation": "sum",
             "column": "revenue",        "group_by": ["region"]},
            {"type": "SortStatement",    "column": "revenue", "direction": "desc"},
        ],
    }


# ------------------------------------------------------------------
# PandasGenerator tests
# ------------------------------------------------------------------

class TestPandasGenerator:

    def test_generate_returns_string(self, load_ast):
        code = PandasGenerator().generate(load_ast)
        assert isinstance(code, str)

    def test_generate_contains_import(self, load_ast):
        code = PandasGenerator().generate(load_ast)
        assert "import pandas as pd" in code

    def test_generate_load_read_csv(self, load_ast):
        code = PandasGenerator().generate(load_ast)
        assert "read_csv" in code
        assert "sales.csv" in code

    def test_generate_compute_groupby(self, compute_ast):
        code = PandasGenerator().generate(compute_ast)
        assert "groupby" in code
        assert "revenue"  in code
        assert "region"   in code

    def test_generate_filter_condition(self, filter_ast):
        code = PandasGenerator().generate(filter_ast)
        assert "region" in code
        assert "West"   in code

    def test_generate_sort_descending(self, sort_ast):
        code = PandasGenerator().generate(sort_ast)
        assert "sort_values" in code
        assert "False"       in code

    def test_generate_chart_bar(self, chart_ast):
        code = PandasGenerator().generate(chart_ast)
        assert "px.bar" in code

    def test_generate_pivot(self, pivot_ast):
        code = PandasGenerator().generate(pivot_ast)
        assert "pivot_table" in code

    def test_op_map_covers_all_operators(self):
        gen = PandasGenerator()
        for op in ["=", "==", "!=", ">", "<", ">=", "<="]:
            assert op in gen.OP_MAP

    def test_agg_map_covers_common_functions(self):
        gen = PandasGenerator()
        for agg in ["sum", "total", "avg", "average", "count", "max", "min"]:
            assert agg in gen.AGG_MAP

    def test_excel_uses_read_excel(self):
        ast  = {
            "type": "Program",
            "body": [{"type": "LoadStatement", "filename": "data.xlsx", "alias": None}],
        }
        code = PandasGenerator().generate(ast)
        assert "read_excel" in code

    def test_multiple_group_by_columns(self):
        ast = {
            "type": "Program",
            "body": [
                {"type": "LoadStatement",    "filename": "sales.csv", "alias": None},
                {"type": "ComputeStatement", "aggregation": "sum",
                 "column": "revenue",        "group_by": ["region", "product"]},
            ],
        }
        code = PandasGenerator().generate(ast)
        assert "region"  in code
        assert "product" in code


# ------------------------------------------------------------------
# SQLGenerator tests
# ------------------------------------------------------------------

class TestSQLGenerator:

    def test_generate_returns_string(self, compute_ast):
        sql = SQLGenerator().generate(compute_ast)
        assert isinstance(sql, str)

    def test_generate_contains_select(self, compute_ast):
        sql = SQLGenerator().generate(compute_ast)
        assert "SELECT" in sql.upper()

    def test_generate_contains_from(self, load_ast):
        sql = SQLGenerator().generate(load_ast)
        assert "FROM" in sql.upper()

    def test_table_name_from_filename(self, load_ast):
        sql = SQLGenerator().generate(load_ast)
        assert "sales" in sql.lower()

    def test_where_clause_generated(self, filter_ast):
        sql = SQLGenerator().generate(filter_ast)
        assert "WHERE" in sql.upper()
        assert "region" in sql.lower()
        assert "West"   in sql

    def test_group_by_clause_generated(self, compute_ast):
        sql = SQLGenerator().generate(compute_ast)
        assert "GROUP BY" in sql.upper()
        assert "region"   in sql.lower()

    def test_agg_function_in_select(self, compute_ast):
        sql = SQLGenerator().generate(compute_ast)
        assert "SUM" in sql.upper()

    def test_order_by_clause(self, sort_ast):
        sql = SQLGenerator().generate(sort_ast)
        assert "ORDER BY" in sql.upper()

    def test_ends_with_semicolon(self, compute_ast):
        sql = SQLGenerator().generate(compute_ast)
        assert sql.strip().endswith(";")

    def test_no_table_returns_comment(self):
        ast = {"type": "Program", "body": []}
        sql = SQLGenerator().generate(ast)
        assert "--" in sql

    def test_generate_create_table(self):
        cols = [
            {"name": "region",  "dtype": "object"},
            {"name": "revenue", "dtype": "float64"},
        ]
        sql = SQLGenerator().generate_create_table("sales.csv", cols)
        assert "CREATE TABLE" in sql.upper()
        assert "region"       in sql
        assert "TEXT"         in sql
        assert "REAL"         in sql

    def test_op_map_covers_natural_language(self):
        gen = SQLGenerator()
        assert "greater than" in gen.OP_MAP
        assert "less than"    in gen.OP_MAP
        assert "at least"     in gen.OP_MAP
        assert "at most"      in gen.OP_MAP


# ------------------------------------------------------------------
# PivotGenerator tests
# ------------------------------------------------------------------

class TestPivotGenerator:

    def test_execute_returns_dataframe(self, sample_df, pivot_ast):
        node   = pivot_ast["body"][1]
        result = PivotGenerator().execute(sample_df, node)
        assert isinstance(result, pd.DataFrame)

    def test_execute_pivot_has_rows(self, sample_df, pivot_ast):
        node   = pivot_ast["body"][1]
        result = PivotGenerator().execute(sample_df, node)
        assert len(result) > 0

    def test_execute_pivot_index_column_present(self, sample_df, pivot_ast):
        node   = pivot_ast["body"][1]
        result = PivotGenerator().execute(sample_df, node)
        assert "product" in [c.lower() for c in result.columns]

    def test_generate_returns_string(self, pivot_ast):
        node = pivot_ast["body"][1]
        code = PivotGenerator().generate(node)
        assert isinstance(code, str)

    def test_generate_contains_pivot_table(self, pivot_ast):
        node = pivot_ast["body"][1]
        code = PivotGenerator().generate(node)
        assert "pivot_table" in code

    def test_generate_styled_contains_background_gradient(self, pivot_ast):
        node = pivot_ast["body"][1]
        code = PivotGenerator().generate_styled(node)
        assert "background_gradient" in code

    def test_infer_index_picks_categorical(self, sample_df):
        gen   = PivotGenerator()
        index = gen._infer_index(sample_df)
        assert index in sample_df.select_dtypes(exclude="number").columns.tolist()

    def test_infer_values_picks_numeric(self, sample_df):
        gen    = PivotGenerator()
        values = gen._infer_values(sample_df)
        assert values in sample_df.select_dtypes(include="number").columns.tolist()

    def test_summarize_returns_dict(self, sample_df, pivot_ast):
        node   = pivot_ast["body"][1]
        pivot  = PivotGenerator().execute(sample_df, node)
        summary = PivotGenerator().summarize(pivot)
        assert isinstance(summary, dict)
        assert "Rows" in summary


# ------------------------------------------------------------------
# JSONGenerator tests
# ------------------------------------------------------------------

class TestJSONGenerator:

    def test_generate_returns_string(self, compute_ast):
        output = JSONGenerator().generate(compute_ast)
        assert isinstance(output, str)

    def test_generate_is_valid_json(self, compute_ast):
        import json
        output = JSONGenerator().generate(compute_ast)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_generate_has_version(self, compute_ast):
        import json
        output = json.loads(JSONGenerator().generate(compute_ast))
        assert "version" in output

    def test_generate_has_panels(self, compute_ast):
        import json
        output = json.loads(JSONGenerator().generate(compute_ast))
        assert "panels" in output
        assert isinstance(output["panels"], list)

    def test_generate_datasource_from_load(self, load_ast):
        import json
        output = json.loads(JSONGenerator().generate(load_ast))
        assert "datasource"          in output
        assert output["datasource"]["filename"] == "sales.csv"

    def test_generate_filters_from_filter(self, filter_ast):
        import json
        output = json.loads(JSONGenerator().generate(filter_ast))
        assert "filters"              in output
        assert output["filters"][0]["column"] == "region"

    def test_generate_chart_panel(self, chart_ast):
        import json
        output = json.loads(JSONGenerator().generate(chart_ast))
        panels = output["panels"]
        chart_panels = [p for p in panels if p["type"] == "chart"]
        assert len(chart_panels) > 0

    def test_generate_pivot_panel(self, pivot_ast):
        import json
        output = json.loads(JSONGenerator().generate(pivot_ast))
        panels = output["panels"]
        pivot_panels = [p for p in panels if p["type"] == "pivot"]
        assert len(pivot_panels) > 0

    def test_generate_from_result_with_dataframe(self, sample_df):
        import json
        result = {
            "output_type":    "dataframe",
            "dataframe":      sample_df,
            "generated_code": "import pandas as pd",
            "code_language":  "python",
            "metrics":        {"Revenue": "4,250"},
            "error":          None,
        }
        output = json.loads(
            JSONGenerator().generate_from_result(result, command="test")
        )
        assert output["command"] == "test"
        assert len(output["panels"]) > 0

    def test_compute_title_with_group_by(self):
        gen  = JSONGenerator()
        node = {"aggregation": "sum", "column": "revenue", "group_by": ["region"]}
        title = gen._compute_title(node)
        assert "region"  in title.lower()
        assert "revenue" in title.lower()

    def test_save_writes_file(self, tmp_path, compute_ast):
        path = str(tmp_path / "dashboard.json")
        JSONGenerator().save(compute_ast, path)
        assert os.path.exists(path)
        with open(path) as f:
            import json
            data = json.load(f)
        assert "panels" in data