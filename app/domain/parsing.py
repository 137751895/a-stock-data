import pandas as pd
from io import StringIO



def parse_ths_eps_table(html_text: str) -> pd.DataFrame:
    """Parse THS HTML to find the EPS forecast table."""
    dfs = pd.read_html(StringIO(html_text))
    for df in dfs:
        cols = [str(c) for c in df.columns]
        if any("每股收益" in c or "均值" in c for c in cols):
            return df
    return dfs[0] if dfs else pd.DataFrame()


def extract_eps_from_df(df: pd.DataFrame) -> dict:
    """Extract eps_cur, eps_next, analyst_count from THS DataFrame."""
    result = {"eps_cur": None, "eps_next": None, "analyst_count": 0}
    if df.empty or len(df.columns) < 3:
        return result
    try:
        for i, row in df.iterrows():
            if i == 0:
                result["eps_cur"] = float(row.iloc[2]) if pd.notna(row.iloc[2]) else None
                result["analyst_count"] = int(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
            elif i == 1:
                result["eps_next"] = float(row.iloc[2]) if pd.notna(row.iloc[2]) else None
            if i >= 1:
                break
    except (ValueError, IndexError):
        pass
    return result
