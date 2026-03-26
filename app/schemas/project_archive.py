from pydantic import BaseModel


class ProjectArchiveAction(BaseModel):
    updated_by: int