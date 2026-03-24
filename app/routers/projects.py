from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.schemas.project import ProjectCreate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
def get_projects():
    query = """
        SELECT
            p.id,
            p.project_number,
            p.name,
            p.kntkarty_id,
            p.kntosoby_id,
            p.owner_user_id,
            u.imie,
            u.nazwisko,
            p.project_type_id,
            pt.name AS project_type_name,
            p.status_id,
            ps.name AS status_name,
            p.stage_id,
            pg.name AS stage_name,
            p.estimated_value_net,
            p.planned_close_date,
            p.actual_close_date,
            p.description,
            p.internal_notes,
            p.is_archived,
            p.created_by,
            p.created_at,
            p.updated_by,
            p.updated_at
        FROM handlowe.projects p
        LEFT JOIN crm.users u
            ON p.owner_user_id = u.id
        LEFT JOIN handlowe.project_types pt
            ON p.project_type_id = pt.id
        LEFT JOIN handlowe.project_statuses ps
            ON p.status_id = ps.id
        LEFT JOIN handlowe.project_stages pg
            ON p.stage_id = pg.id
        ORDER BY p.id DESC
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        items = [dict(zip(columns, row)) for row in rows]
        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_project(project: ProjectCreate):
    query = """
        INSERT INTO handlowe.projects (
            project_number,
            name,
            kntkarty_id,
            kntosoby_id,
            owner_user_id,
            project_type_id,
            status_id,
            stage_id,
            estimated_value_net,
            planned_close_date,
            description,
            internal_notes,
            created_by,
            created_at,
            is_archived
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            NOW(),
            false
        )
        RETURNING id;
    """

    values = (
        project.project_number,
        project.name,
        project.kntkarty_id,
        project.kntosoby_id,
        project.owner_user_id,
        project.project_type_id,
        project.status_id,
        project.stage_id,
        project.estimated_value_net,
        project.planned_close_date,
        project.description,
        project.internal_notes,
        project.created_by
    )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                new_id = cur.fetchone()[0]
            conn.commit()

        return {
            "message": "Projekt został utworzony",
            "id": new_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))