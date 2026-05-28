import math


def forward_pe(price: float, eps_forecast: float) -> float:
    """Forward PE = current price / forecast EPS."""
    if eps_forecast <= 0:
        return float("inf")
    return price / eps_forecast


def pe_digestion(current_pe: float, cagr: float, target_pe: float = 30.0) -> float:
    """Years to digest current PE to target PE.

    target_pe defaults to 30x (A-share growth stock anchor).
    cagr: next year EPS / current year EPS - 1
    """
    if current_pe <= target_pe:
        return 0.0
    if cagr <= 0:
        return float("inf")
    return math.log(current_pe / target_pe) / math.log(1 + cagr)


def calc_peg(pe: float, cagr: float) -> float:
    """PEG = forward PE / (CAGR * 100).

    PEG < 1   → cheap
    PEG 1-1.5 → fair
    PEG > 1.5 → expensive
    """
    if cagr <= 0:
        return float("inf")
    return pe / (cagr * 100)
