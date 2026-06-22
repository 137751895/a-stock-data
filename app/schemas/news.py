from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str = ""
    content: str = ""
    time: str = ""
    source: str = ""
    url: str = ""
