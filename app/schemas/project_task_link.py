from pydantic import BaseModel


class ProjectTaskLinkCreate(BaseModel):
    project_id: int
    task_id: int
    linked_by_user_id: int