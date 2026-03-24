from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    project_number: str
    name: str
    kntkarty_id: int
    owner_user_id: int
    status_id: int
    stage_id: int

    kntosoby_id: Optional[int] = None
    project_type_id: Optional[int] = None
    estimated_value_net: Optional[Decimal] = None
    planned_close_date: Optional[date] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    created_by: Optional[int] = None