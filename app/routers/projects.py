from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.schemas.project import ProjectCreate
from app.schemas.project import ProjectCreate, ProjectUpdate

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


@router.get("/{project_id}")
def get_project_by_id(project_id: int):
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
            u.email,
            u.telefon,
            p.project_type_id,
            pt.name AS project_type_name,
            p.status_id,
            ps.name AS status_name,
            ps.color AS status_color,
            ps.is_closed AS status_is_closed,
            p.stage_id,
            pg.name AS stage_name,
            pg.sort_order AS stage_sort_order,
            pg.is_closed AS stage_is_closed,
            pg.is_won AS stage_is_won,
            pg.is_lost AS stage_is_lost,
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
        WHERE p.id = %s
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (project_id,))
                row = cur.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                columns = [desc[0] for desc in cur.description]

        item = dict(zip(columns, row))
        return item

    except HTTPException:
        raise
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
    
@router.put("/{project_id}")
def update_project(project_id: int, project: ProjectUpdate):
    check_query = """
        SELECT id
        FROM handlowe.projects
        WHERE id = %s
    """

    update_query = """
        UPDATE handlowe.projects
        SET
            project_number = %s,
            name = %s,
            kntkarty_id = %s,
            kntosoby_id = %s,
            owner_user_id = %s,
            project_type_id = %s,
            status_id = %s,
            stage_id = %s,
            estimated_value_net = %s,
            planned_close_date = %s,
            actual_close_date = %s,
            description = %s,
            internal_notes = %s,
            is_archived = %s,
            updated_by = %s,
            updated_at = NOW()
        WHERE id = %s
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_query, (project_id,))
                existing = cur.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                cur.execute(
                    update_query,
                    (
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
                        project.actual_close_date,
                        project.description,
                        project.internal_notes,
                        project.is_archived,
                        project.updated_by,
                        project_id
                    )
                )
            conn.commit()

        return {
            "message": "Projekt został zaktualizowany",
            "id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))