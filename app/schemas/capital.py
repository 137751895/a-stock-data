from pydantic import BaseModel


class FundFlowItem(BaseModel):
    time: str = ""
    main_net: float = 0
    small_net: float = 0
    mid_net: float = 0
    large_net: float = 0
    super_net: float = 0


class MarginItem(BaseModel):
    """Margin trading daily record per SKILL.md semantics."""
    date: str = ""
    rzye: float = 0       # 融资余额(元)
    rzmre: float = 0      # 融资买入额
    rzche: float = 0      # 融资偿还额
    rqye: float = 0       # 融券余额(元)
    rqmcl: float = 0      # 融券卖出量
    rqchl: float = 0      # 融券偿还量
    rzrqye: float = 0     # 融资融券余额合计
