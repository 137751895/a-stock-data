from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_fund_flow_minute, fetch_margin_trading


def get_fund_flow_minute(code: str) -> list[dict]:
    """Get minute-level fund flow for a stock."""
    code = validate_code(code)
    return fetch_fund_flow_minute(code)


def get_margin_trading(code: str) -> list[dict]:
    """Get margin trading data for a stock."""
    code = validate_code(code)
    return fetch_margin_trading(code)
