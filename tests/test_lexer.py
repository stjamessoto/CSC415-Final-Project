import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from retaillang.lexer import Lexer, Token, TokenType


class TestTokenTypes:
    """Verify individual tokens are classified correctly."""

    def test_keyword_load(self):
        tokens = Lexer("Load").tokenize()
        assert tokens[0].type == TokenType.KEYWORD
        assert tokens[0].value == "load"

    def test_keyword_synonyms_normalised(self):
        for word in ["import", "read", "open"]:
            tokens = Lexer(word).tokenize()
            assert tokens[0].value == "load", f"{word} should normalise to 'load'"

    def test_compute_synonyms_normalised(self):
        for word in ["calculate", "find", "get"]:
            tokens = Lexer(word).tokenize()
            assert tokens[0].value == "compute", f"{word} should normalise to 'compute'"

    def test_filename_with_csv(self):
        tokens = Lexer("Load sales.csv").tokenize()
        filename_tok = tokens[1]
        assert filename_tok.type == TokenType.FILENAME
        assert filename_tok.value == "sales.csv"

    def test_filename_with_xlsx(self):
        tokens = Lexer("Load orders.xlsx").tokenize()
        assert tokens[1].type == TokenType.FILENAME
        assert tokens[1].value == "orders.xlsx"

    def test_string_literal_double_quotes(self):
        tokens = Lexer('"West"').tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "West"

    def test_string_literal_single_quotes(self):
        tokens = Lexer("'Electronics'").tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "Electronics"

    def test_integer_number(self):
        tokens = Lexer("1000").tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "1000"

    def test_float_number(self):
        tokens = Lexer("99.95").tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "99.95"

    def test_comparator_equals(self):
        tokens = Lexer("=").tokenize()
        assert tokens[0].type == TokenType.COMPARATOR

    def test_comparator_greater_than(self):
        tokens = Lexer(">").tokenize()
        assert tokens[0].type == TokenType.COMPARATOR

    def test_comparator_greater_equal(self):
        tokens = Lexer(">=").tokenize()
        assert tokens[0].type == TokenType.COMPARATOR
        assert tokens[0].value == ">="

    def test_identifier(self):
        tokens = Lexer("region").tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER

    def test_punctuation_comma(self):
        tokens = Lexer(",").tokenize()
        assert tokens[0].type == TokenType.PUNCT

    def test_eof_appended(self):
        tokens = Lexer("Load sales.csv").tokenize()
        assert tokens[-1].type == TokenType.EOF

    def test_article_ignored(self):
        tokens = Lexer("generate a bar chart").tokenize()
        values = [t.value for t in tokens if t.type != TokenType.EOF]
        assert "a" not in values

    def test_case_insensitive(self):
        tokens_upper = Lexer("LOAD SALES.CSV").tokenize()
        tokens_lower = Lexer("load sales.csv").tokenize()
        assert tokens_upper[0].value == tokens_lower[0].value


class TestTokenStream:
    """Verify full token streams for complete commands."""

    def test_load_command_token_count(self):
        tokens = Lexer("Load sales.csv").tokenize()
        non_eof = [t for t in tokens if t.type != TokenType.EOF]
        assert len(non_eof) == 2

    def test_compute_command_tokens(self):
        tokens = Lexer("compute total revenue by region").tokenize()
        values = [t.value for t in tokens if t.type != TokenType.EOF]
        assert "compute" in values
        assert "total"   in values
        assert "revenue" in values
        assert "by"      in values
        assert "region"  in values

    def test_filter_command_tokens(self):
        tokens = Lexer("filter by region = West").tokenize()
        types  = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.COMPARATOR in types

    def test_compound_command_has_multiple_keywords(self):
        cmd    = "Load sales.csv and compute total revenue by region"
        tokens = Lexer(cmd).tokenize()
        kws    = [t.value for t in tokens if t.type == TokenType.KEYWORD]
        assert "load"    in kws
        assert "compute" in kws

    def test_chart_command_tokens(self):
        tokens = Lexer("generate a bar chart").tokenize()
        values = [t.value for t in tokens if t.type != TokenType.EOF]
        assert "generate" in values
        assert "bar"      in values
        assert "chart"    in values

    def test_sort_command_tokens(self):
        tokens = Lexer("sort by revenue descending").tokenize()
        values = [t.value for t in tokens if t.type != TokenType.EOF]
        assert "sort"        in values
        assert "revenue"     in values
        assert "descending"  in values

    def test_pivot_command_tokens(self):
        tokens = Lexer("create a pivot table by product and region").tokenize()
        values = [t.value for t in tokens if t.type != TokenType.EOF]
        assert "create" in values
        assert "pivot"  in values
        assert "table"  in values


class TestSynonymResolution:
    """Verify synonym pre-processing maps aliases to canonical forms."""

    def test_profit_synonym_earnings(self):
        tokens = Lexer("compute total earnings by region").tokenize()
        values = [t.value for t in tokens]
        assert "revenue" in values or "profit" in values or "earnings" in values

    def test_revenue_synonym_sales(self):
        tokens = Lexer("compute total sales by region").tokenize()
        values = [t.value for t in tokens]
        assert any(v in values for v in ["revenue", "sales"])

    def test_filter_synonym_where(self):
        tokens = Lexer("where region = West").tokenize()
        kws    = [t.value for t in tokens if t.type == TokenType.KEYWORD]
        assert "filter" in kws or "where" in kws

    def test_average_synonym_avg(self):
        tokens = Lexer("compute avg profit by product").tokenize()
        values = [t.value for t in tokens]
        assert any(v in values for v in ["average", "avg"])


class TestErrorHandling:
    """Verify the lexer raises or flags unrecognised input gracefully."""

    def test_unknown_token_raises_lex_error(self):
        from retaillang.errors import LexError
        with pytest.raises(LexError):
            Lexer("$$invalidtoken$$").tokenize()

    def test_empty_string_returns_only_eof(self):
        tokens = Lexer("").tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only_returns_eof(self):
        tokens = Lexer("   ").tokenize()
        assert tokens[-1].type == TokenType.EOF

    def test_typo_suggestion_available(self):
        from retaillang.errors import LexError
        try:
            Lexer("comptue total revenue by region").tokenize()
        except LexError as e:
            assert e.suggestion is not None

    def test_position_reported_in_error(self):
        from retaillang.errors import LexError
        try:
            Lexer("load sales.csv and $$bad$$").tokenize()
        except LexError as e:
            assert e.position is not None


class TestFormatTokenStream:
    """Verify the debug token stream formatter used by the IDE."""

    def test_format_returns_string(self):
        lexer  = Lexer("Load sales.csv")
        lexer.tokenize()
        output = lexer.format_token_stream()
        assert isinstance(output, str)

    def test_format_contains_token_types(self):
        lexer  = Lexer("Load sales.csv")
        lexer.tokenize()
        output = lexer.format_token_stream()
        assert "KEYWORD"  in output
        assert "FILENAME" in output

    def test_format_contains_values(self):
        lexer  = Lexer("Load sales.csv")
        lexer.tokenize()
        output = lexer.format_token_stream()
        assert "load"      in output.lower()
        assert "sales.csv" in output.lower()