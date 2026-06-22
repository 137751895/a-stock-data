from app.core.http import http_get
from app.core.normalize import to_tencent_symbol
from app.core.errors import UpstreamSchemaError


def fetch_quotes(codes: list[str]) -> dict[str, dict]:
    """Fetch real-time quotes from Tencent Finance API.

    Returns: {code: {name, price, pe_ttm, pb, mcap_yi, ...}}
    """
    symbols = [to_tencent_symbol(c) for c in codes]
    url = "https://qt.gtimg.cn/q=" + ",".join(symbols)
    r = http_get(url, timeout=10, provider="tencent")
    try:
        data = r.content.decode("gbk")
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to decode Tencent response: {e}", provider="tencent")

    return parse_tencent_response(data)


def parse_tencent_response(data: str) -> dict[str, dict]:
    """Parse raw Tencent quote response into structured dict."""
    result = {}
    for line in data.strip().split(";"):
        if not line.strip() or "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        code = key[2:]
        result[code] = parse_tencent_fields(vals)
    return result


def parse_tencent_fields(vals: list[str]) -> dict:
    """Parse tencent ~-separated fields into a dict.

    Critical field mapping (verified 2026-05-03):
    - 43 = amplitude_pct (NOT PB!)
    - 46 = pb
    """
    return {
        "name": vals[1],
        "price": _float(vals[3]),
        "last_close": _float(vals[4]),
        "open": _float(vals[5]),
        "change_amt": _float(vals[31]),
        "change_pct": _float(vals[32]),
        "high": _float(vals[33]),
        "low": _float(vals[34]),
        "amount_wan": _float(vals[37]),
        "turnover_pct": _float(vals[38]),
        "pe_ttm": _float(vals[39]),
        "amplitude_pct": _float(vals[43]),  # NOT PB!
        "mcap_yi": _float(vals[44]),
        "float_mcap_yi": _float(vals[45]),
        "pb": _float(vals[46]),  # PB is at index 46
        "limit_up": _float(vals[47]),
        "limit_down": _float(vals[48]),
        "vol_ratio": _float(vals[49]),
        "pe_static": _float(vals[52]),
    }


def _float(val: str) -> float:
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0
