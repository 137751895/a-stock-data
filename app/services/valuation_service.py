
from app.core.errors import AppError
from app.core.normalize import validate_code
from app.domain.parsing import parse_ths_eps_table, extract_eps_from_df
from app.domain.valuation import forward_pe, pe_digestion, calc_peg
from app.providers.tencent import fetch_quotes
from app.providers.ths import fetch_eps_forecast

# Errors that are safe to degrade into warnings (partial availability).
# AppError covers all upstream HTTP/schema/auth errors.
# Network-level errors may also occur outside our http wrapper.
_DEGRADABLE = (AppError, ConnectionError, TimeoutError, ValueError)


def get_valuation(code: str) -> dict:
    """Get full valuation for a stock.

    Aggregates Tencent quote + THS EPS forecast + valuation calculations.
    Returns partial results with warnings if some sources fail.
    Programming errors (TypeError, KeyError, etc.) are NOT swallowed.
    """
    code = validate_code(code)
    warnings = []
    result = {"code": code}

    # 1. Tencent quote
    try:
        quotes = fetch_quotes([code])
        quote = quotes.get(code, {})
        result["name"] = quote.get("name", "")
        result["price"] = quote.get("price", 0)
        result["mcap_yi"] = quote.get("mcap_yi", 0)
        result["pe_ttm"] = quote.get("pe_ttm", 0)
        result["pb"] = quote.get("pb", 0)
    except _DEGRADABLE as e:
        warnings.append(f"Failed to fetch quote: {e}")
        result["price"] = 0

    # 2. THS EPS forecast
    eps_data = {"eps_cur": None, "eps_next": None, "analyst_count": 0}
    try:
        ths_result = fetch_eps_forecast(code)
        df = parse_ths_eps_table(ths_result["html"])
        eps_data = extract_eps_from_df(df)
    except _DEGRADABLE as e:
        warnings.append(f"Failed to fetch EPS forecast: {e}")

    result["eps_cur"] = eps_data["eps_cur"]
    result["eps_next"] = eps_data["eps_next"]
    result["analyst_count"] = eps_data["analyst_count"]

    # 3. Valuation calculations
    price = result.get("price", 0)
    eps_cur = eps_data["eps_cur"]
    eps_next = eps_data["eps_next"]

    if eps_cur and eps_cur > 0 and price:
        pe_fwd = forward_pe(price, eps_cur)
        result["pe_fwd"] = round(pe_fwd, 1) if pe_fwd != float("inf") else None
    else:
        result["pe_fwd"] = None
        if not eps_cur:
            warnings.append("EPS forecast unavailable, cannot compute forward PE")

    if eps_cur and eps_next and eps_cur > 0:
        cagr = eps_next / eps_cur - 1
        result["cagr_pct"] = round(cagr * 100, 1) if cagr else None

        if cagr > 0 and result.get("pe_fwd"):
            result["peg"] = round(calc_peg(result["pe_fwd"], cagr), 2)
            result["digest_years"] = round(pe_digestion(result["pe_fwd"], cagr), 1)
        else:
            result["peg"] = None
            result["digest_years"] = None
    else:
        result["cagr_pct"] = None
        result["peg"] = None
        result["digest_years"] = None

    return {"data": result, "warnings": warnings, "source": ["tencent", "10jqka"]}
