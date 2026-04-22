import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retaillang.lexer    import Lexer
from retaillang.parser   import Parser
from retaillang.executor import Executor


@pytest.fixture(scope="module")
def sample_df():
    """Create a small in-memory DataFrame that mirrors the data CSVs."""
    return pd.DataFrame({
        "region":   ["West", "West", "East", "East", "North"],
        "product":  ["Laptop", "Phone", "Laptop", "Tablet", "Phone"],
        "category": ["Electronics", "Electronics", "Electronics", "Electronics", "Electronics"],
        "revenue":  [1200.0, 800.0, 950.0, 600.0, 700.0],
        "profit":   [300.0, 150.0, 200.0, 100.0, 120.0],
        "units":    [10, 20, 15, 8, 12],
    })


@pytest.fixture(scope="module")
def sample_csv_path(tmp_path_factory, sample_df):
    """Write the sample DataFrame to a temp CSV named sales.csv and return its path."""
    path = tmp_path_factory.mktemp("data") / "sales.csv"
    sample_df.to_csv(path, index=False)
    return str(path)


def run(command: str, csv_path: str) -> dict:
    """Helper: substitute 'sales.csv' in command with the real temp path, then run pipeline."""
    command = command.replace("sales.csv", csv_path)
    tokens  = Lexer(command).tokenize()
    ast     = Parser(tokens).parse()
    return Executor().execute(ast)


class TestLoadExecution:

    def test_load_returns_no_error(self, sample_csv_path):
        result = run("Load sales.csv", sample_csv_path)
        assert result.get("error") is None

    def test_load_nonexistent_file_returns_error(self):
        tokens = Lexer("Load nonexistent_file.csv").tokenize()
        ast    = Parser(tokens).parse()
        result = Executor().execute(ast)
        assert result.get("error") is not None


class TestFilterExecution:

    def test_filter_equals(self, sample_csv_path):
        result = run("Load sales.csv filter by region = West", sample_csv_path)
        df = result.get("dataframe")
        if df is not None:
            assert all(df["region"].str.lower() == "west")

    def test_filter_greater_than(self, sample_csv_path):
        result = run("Load sales.csv filter by profit > 150", sample_csv_path)
        df = result.get("dataframe")
        if df is not None:
            assert all(df["profit"] > 150)

    def test_filter_reduces_rows(self, sample_csv_path):
        result_all  = run("Load sales.csv", sample_csv_path)
        result_west = run("Load sales.csv filter by region = West", sample_csv_path)
        df_all  = result_all.get("dataframe")
        df_west = result_west.get("dataframe")
        if df_all is not None and df_west is not None:
            assert len(df_west) < len(df_all)

    def test_filter_and_condition(self, sample_csv_path):
        result = run(
            "Load sales.csv filter by region = West and profit > 100",
            sample_csv_path,
        )
        assert result.get("error") is None


class TestComputeExecution:

    def test_compute_total_revenue(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total revenue by region",
            sample_csv_path,
        )
        assert result.get("error")       is None
        assert result.get("output_type") == "dataframe"
        df = result.get("dataframe")
        assert df is not None
        assert len(df) > 0

    def test_compute_average_profit(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute average profit by product",
            sample_csv_path,
        )
        assert result.get("error") is None
        df = result.get("dataframe")
        assert df is not None

    def test_compute_result_has_group_column(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total revenue by region",
            sample_csv_path,
        )
        df = result.get("dataframe")
        if df is not None:
            assert "region" in [c.lower() for c in df.columns]

    def test_compute_result_has_value_column(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total revenue by region",
            sample_csv_path,
        )
        df = result.get("dataframe")
        if df is not None:
            cols = [c.lower() for c in df.columns]
            assert any("revenue" in c for c in cols)

    def test_compute_count(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute count of units by region",
            sample_csv_path,
        )
        assert result.get("error") is None

    def test_compute_metrics_populated(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total revenue by region",
            sample_csv_path,
        )
        assert isinstance(result.get("metrics"), dict)
        assert len(result["metrics"]) > 0


class TestSortExecution:

    def test_sort_descending(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total revenue by region "
            "and sort by revenue descending",
            sample_csv_path,
        )
        assert result.get("error") is None
        df = result.get("dataframe")
        if df is not None and len(df) > 1:
            revenue_col = [c for c in df.columns if "revenue" in c.lower()][0]
            values = df[revenue_col].tolist()
            assert values == sorted(values, reverse=True)

    def test_sort_ascending(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total profit by product "
            "and sort by profit ascending",
            sample_csv_path,
        )
        assert result.get("error") is None


class TestChartExecution:

    def test_chart_returns_figure(self, sample_csv_path):
        result = run(
            "Load sales.csv, compute total revenue by region, "
            "and generate a bar chart",
            sample_csv_path,
        )
        assert result.get("error")       is None
        assert result.get("output_type") == "chart"
        assert result.get("figure")      is not None

    def test_line_chart(self, sample_csv_path):
        result = run(
            "Load sales.csv, compute total revenue by region, "
            "and generate a line chart",
            sample_csv_path,
        )
        assert result.get("output_type") == "chart"

    def test_chart_without_compute_does_not_crash(self, sample_csv_path):
        result = run("Load sales.csv and generate a bar chart", sample_csv_path)
        assert isinstance(result, dict)


class TestPivotExecution:

    def test_pivot_returns_dataframe(self, sample_csv_path):
        result = run(
            "Load sales.csv and create a pivot table by product and region",
            sample_csv_path,
        )
        assert result.get("error")       is None
        assert result.get("output_type") == "pivot"
        assert result.get("dataframe")   is not None

    def test_pivot_shape(self, sample_csv_path):
        result = run(
            "Load sales.csv and create a pivot table by product and region",
            sample_csv_path,
        )
        df = result.get("dataframe")
        if df is not None:
            assert df.shape[0] > 0
            assert df.shape[1] > 1


class TestCompoundExecution:

    def test_full_pipeline(self, sample_csv_path):
        result = run(
            "Load sales.csv, filter by region = West, "
            "compute total revenue by product, and generate a bar chart",
            sample_csv_path,
        )
        assert result.get("error")       is None
        assert result.get("output_type") == "chart"

    def test_filter_then_compute(self, sample_csv_path):
        result = run(
            "Load sales.csv, filter by profit > 100, "
            "and compute total revenue by region",
            sample_csv_path,
        )
        assert result.get("error")       is None
        assert result.get("output_type") == "dataframe"

    def test_generated_code_returned(self, sample_csv_path):
        result = run(
            "Load sales.csv and compute total revenue by region",
            sample_csv_path,
        )
        code = result.get("generated_code", "")
        assert "import pandas" in code
        assert "groupby"       in code

    def test_error_on_compute_before_load(self):
        tokens = Lexer("compute total revenue by region").tokenize()
        ast    = Parser(tokens).parse()
        result = Executor().execute(ast)
        assert result.get("error") is not None
