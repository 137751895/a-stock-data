import re


def normalize_code(code: str) -> str:
    """Normalize stock code to pure 6-digit format.

    Supports inputs like: 688017, SH688017, sh688017, 688017.SH, SZ000001, BJ832000
    """
    code = code.strip().upper()
    # Remove prefix: SH/SZ/BJ
    match = re.match(r"^(SH|SZ|BJ)(\d{6})$", code)
    if match:
        return match.group(2)
    # Remove suffix: .SH/.SZ/.BJ
    match = re.match(r"^(\d{6})\.(SH|SZ|BJ)$", code)
    if match:
        return match.group(1)
    # Already pure digits
    match = re.match(r"^(\d{6})$", code)
    if match:
        return match.group(1)
    return code


def get_prefix(code: str) -> str:
    """6-digit code -> market prefix (sh/sz/bj)."""
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith("8"):
        return "bj"
    else:
        return "sz"


def to_tencent_symbol(code: str) -> str:
    """6-digit code -> tencent symbol like sh600519."""
    code = normalize_code(code)
    return f"{get_prefix(code)}{code}"


def to_eastmoney_secid(code: str) -> str:
    """6-digit code -> eastmoney secid like 1.600519."""
    code = normalize_code(code)
    market_code = 1 if code.startswith("6") else 0
    return f"{market_code}.{code}"


def to_cninfo_org_id(code: str) -> str:
    """6-digit code -> cninfo orgId like gssh0600519."""
    code = normalize_code(code)
    if code.startswith("6"):
        return f"gssh0{code}"
    elif code.startswith(("8", "4")):
        return f"gsbj0{code}"
    else:
        return f"gssz0{code}"
