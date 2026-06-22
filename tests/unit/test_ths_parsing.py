"""Unit tests for THS HTML parsing (domain/parsing.py)."""
import pandas as pd

from app.domain.parsing import parse_ths_eps_table, extract_eps_from_df


class TestParseThsEpsTable:
    def test_finds_eps_table(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>年度</th><th>机构数</th><th>每股收益(均值)</th></tr></thead>
            <tbody>
                <tr><td>2026</td><td>25</td><td>60.50</td></tr>
                <tr><td>2027</td><td>20</td><td>78.00</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        df = parse_ths_eps_table(html)
        assert not df.empty
        assert len(df) >= 2

    def test_returns_first_table_when_no_eps_keyword(self):
        html = """
        <html><body>
        <table>
            <thead><tr><th>A</th><th>B</th></tr></thead>
            <tbody><tr><td>1</td><td>2</td></tr></tbody>
        </table>
        </body></html>
        """
        df = parse_ths_eps_table(html)
        assert not df.empty

    def test_returns_empty_df_when_no_tables(self):
        html = "<html><body><p>No tables here</p></body></html>"
        # When no tables exist, pd.read_html raises or returns empty
        # The calling code (valuation_service) catches this via try/except
        import pytest
        with pytest.raises(Exception):
            parse_ths_eps_table(html)


class TestExtractEpsFromDf:
    def test_normal_extraction(self):
        df = pd.DataFrame({
            "年度": ["2026", "2027"],
            "机构数": [25, 20],
            "每股收益(均值)": [60.50, 78.00],
        })
        result = extract_eps_from_df(df)
        assert result["eps_cur"] == 60.50
        assert result["eps_next"] == 78.00
        assert result["analyst_count"] == 25

    def test_empty_df_returns_none(self):
        result = extract_eps_from_df(pd.DataFrame())
        assert result["eps_cur"] is None
        assert result["eps_next"] is None
        assert result["analyst_count"] == 0

    def test_too_few_columns_returns_none(self):
        df = pd.DataFrame({"A": [1, 2]})
        result = extract_eps_from_df(df)
        assert result["eps_cur"] is None

    def test_nan_values_handled(self):
        df = pd.DataFrame({
            "年度": ["2026", "2027"],
            "机构数": [None, None],
            "每股收益(均值)": [None, None],
        })
        result = extract_eps_from_df(df)
        assert result["eps_cur"] is None
        assert result["analyst_count"] == 0

    def test_single_row_only_gets_eps_cur(self):
        df = pd.DataFrame({
            "年度": ["2026"],
            "机构数": [25],
            "每股收益(均值)": [60.50],
        })
        result = extract_eps_from_df(df)
        assert result["eps_cur"] == 60.50
        assert result["eps_next"] is None
