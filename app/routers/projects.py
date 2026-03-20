from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
def get_projects():
    return {
        "items": [
            {"id": 1, "name": "Projekt testowy 1"},
            {"id": 2, "name": "Projekt testowy 2"}
        ]
    }