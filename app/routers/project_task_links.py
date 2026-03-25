from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from app.schemas.project_task_link import ProjectTaskLinkCreate

router = APIRouter(prefix="/project-task-links", tags=["project-task-links"])


@router.get("/")
def get_project_task_links(project_id: int = Query(...)):
    query = """
        SELECT
            ptl.id,
            ptl.project_id,
            ptl.task_id,
            ptl.linked_at,
            ptl.linked_by_user_id,
            lu.imie AS linked_by_imie,
            lu.nazwisko AS linked_by_nazwisko,
            t.nazwa AS task_name,
            t.opis AS task_description,
            t.status AS task_status,
            t.czas_utworzenia,
            t.czas_modyfikacji,
            t.czas_rozpoczecia,
            t.czas_zakonczenia,
            t.tworca_id,
            t.wykonawca_id,
            u.imie AS wykonawca_imie,
            u.nazwisko AS wykonawca_nazwisko
        FROM handlowe.project_task_links ptl
        LEFT JOIN crm.tasks t
            ON ptl.task_id = t.id
        LEFT JOIN crm.users u
            ON t.wykonawca_id = u.id
        LEFT JOIN crm.users lu
            ON ptl.linked_by_user_id = lu.id
        WHERE ptl.project_id = %s
        ORDER BY ptl.id DESC
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (project_id,))
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        items = [dict(zip(columns, row)) for row in rows]
        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_project_task_link(link: ProjectTaskLinkCreate):
    check_project_query = """
        SELECT id
        FROM handlowe.projects
        WHERE id = %s
    """

    check_task_query = """
        SELECT id
        FROM crm.tasks
        WHERE id = %s
          AND COALESCE(is_deleted, false) = false
    """

    check_user_query = """
        SELECT id
        FROM crm.users
        WHERE id = %s
          AND COALESCE(is_delete, false) = false
    """

    check_duplicate_query = """
        SELECT id
        FROM handlowe.project_task_links
        WHERE project_id = %s
          AND task_id = %s
    """

    insert_query = """
        INSERT INTO handlowe.project_task_links (
            project_id,
            task_id,
            linked_at,
            linked_by_user_id
        )
        VALUES (%s, %s, NOW(), %s)
        RETURNING id
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_project_query, (link.project_id,))
                existing_project = cur.fetchone()
                if not existing_project:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                cur.execute(check_task_query, (link.task_id,))
                existing_task = cur.fetchone()
                if not existing_task:
                    raise HTTPException(status_code=404, detail="Task nie istnieje")

                cur.execute(check_user_query, (link.linked_by_user_id,))
                existing_user = cur.fetchone()
                if not existing_user:
                    raise HTTPException(status_code=404, detail="Użytkownik linkujący nie istnieje")

                cur.execute(check_duplicate_query, (link.project_id, link.task_id))
                existing_link = cur.fetchone()
                if existing_link:
                    raise HTTPException(status_code=400, detail="Ten task jest już przypięty do projektu")

                cur.execute(
                    insert_query,
                    (link.project_id, link.task_id, link.linked_by_user_id)
                )
                new_id = cur.fetchone()[0]

            conn.commit()

        return {
            "message": "Task został przypięty do projektu",
            "id": new_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{link_id}")
def delete_project_task_link(link_id: int):
    check_query = """
        SELECT id
        FROM handlowe.project_task_links
        WHERE id = %s
    """

    delete_query = """
        DELETE FROM handlowe.project_task_links
        WHERE id = %s
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_query, (link_id,))
                existing = cur.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Link taska nie istnieje")

                cur.execute(delete_query, (link_id,))

            conn.commit()

        return {
            "message": "Link taska został usunięty",
            "id": link_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))