from pydantic import BaseModel


class StockInfo(BaseModel):
    code: str = ""
    name: str = ""
    industry: str = ""
    total_shares: float = 0
    float_shares: float = 0
    mcap: float = 0
    float_mcap: float = 0
    list_date: str = ""
    price: float = 0
