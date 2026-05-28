from pydantic import BaseModel


class ReportItem(BaseModel):
    title: str = ""
    publishDate: str = ""
    orgSName: str = ""
    infoCode: str = ""
    stockName: str = ""
    stockCode: str = ""
    predictThisYearEps: float | None = None
    predictNextYearEps: float | None = None
    emRatingName: str = ""
