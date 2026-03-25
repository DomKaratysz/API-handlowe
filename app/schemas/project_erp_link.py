from pydantic import BaseModel
from typing import Optional


class ProjectErpLinkCreate(BaseModel):
    project_id: int
    source_type: Optional[str] = None
    gidtyp: int
    gidfirma: str
    gidnumer: int
    gidlp: int
    name: Optional[str] = None