from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/")
def get_tasks():
    return {
        "items": [
            {"id": 1, "name": "Task testowy 1"},
            {"id": 2, "name": "Task testowy 2"}
        ]
    }