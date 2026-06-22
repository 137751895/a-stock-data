from pydantic import BaseModel


class QuoteItem(BaseModel):
    name: str = ""
    price: float = 0
    last_close: float = 0
    open: float = 0
    change_amt: float = 0
    change_pct: float = 0
    high: float = 0
    low: float = 0
    amount_wan: float = 0
    turnover_pct: float = 0
    pe_ttm: float = 0
    amplitude_pct: float = 0
    mcap_yi: float = 0
    float_mcap_yi: float = 0
    pb: float = 0
    limit_up: float = 0
    limit_down: float = 0
    vol_ratio: float = 0
    pe_static: float = 0
