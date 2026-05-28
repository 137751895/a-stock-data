from pydantic import BaseModel


class ValuationData(BaseModel):
    code: str = ""
    name: str = ""
    price: float = 0
    mcap_yi: float = 0
    pe_ttm: float = 0
    pb: float = 0
    eps_cur: float | None = None
    eps_next: float | None = None
    analyst_count: int = 0
    pe_fwd: float | None = None
    cagr_pct: float | None = None
    peg: float | None = None
    digest_years: float | None = None
