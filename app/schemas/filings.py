from pydantic import BaseModel


class AnnouncementItem(BaseModel):
    title: str = ""
    type: str = ""
    date: str = ""
    url: str = ""
