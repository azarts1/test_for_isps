from pydantic import BaseModel


class ArchiveUrl(BaseModel):
    url: str
    file_name: str | None
