from pydantic import BaseModel


class ProjectTeamCreate(BaseModel):
    project_id: int
    user_id: int