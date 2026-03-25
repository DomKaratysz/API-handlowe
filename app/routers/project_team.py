from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from app.schemas.project_team import ProjectTeamCreate

router = APIRouter(prefix="/project-team", tags=["project-team"])


@router.get("/")
def get_project_team(project_id: int = Query(...)):
    query = """
        SELECT
            pt.id,
            pt.project_id,
            pt.user_id,
            pt.added_at,
            u.imie,
            u.nazwisko,
            u.email,
            u.telefon,
            u.stanowisko,
            u.dzial,
            u.oddzial,
            u.is_admin
        FROM handlowe.project_team pt
        LEFT JOIN crm.users u
            ON pt.user_id = u.id
        WHERE pt.project_id = %s
        ORDER BY u.nazwisko, u.imie, pt.id
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
def create_project_team(link: ProjectTeamCreate):
    check_project_query = """
        SELECT id
        FROM handlowe.projects
        WHERE id = %s
    """

    check_user_query = """
        SELECT id
        FROM crm.users
        WHERE id = %s
          AND COALESCE(is_delete, false) = false
    """

    check_duplicate_query = """
        SELECT id
        FROM handlowe.project_team
        WHERE project_id = %s
          AND user_id = %s
    """

    insert_query = """
        INSERT INTO handlowe.project_team (
            project_id,
            user_id,
            added_at
        )
        VALUES (%s, %s, NOW())
        RETURNING id
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_project_query, (link.project_id,))
                existing_project = cur.fetchone()
                if not existing_project:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                cur.execute(check_user_query, (link.user_id,))
                existing_user = cur.fetchone()
                if not existing_user:
                    raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

                cur.execute(check_duplicate_query, (link.project_id, link.user_id))
                existing_link = cur.fetchone()
                if existing_link:
                    raise HTTPException(status_code=400, detail="Ten użytkownik jest już w zespole projektu")

                cur.execute(insert_query, (link.project_id, link.user_id))
                new_id = cur.fetchone()[0]

            conn.commit()

        return {
            "message": "Użytkownik został dodany do zespołu projektu",
            "id": new_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{team_id}")
def delete_project_team_member(team_id: int):
    check_query = """
        SELECT id
        FROM handlowe.project_team
        WHERE id = %s
    """

    delete_query = """
        DELETE FROM handlowe.project_team
        WHERE id = %s
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_query, (team_id,))
                existing = cur.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Członek zespołu nie istnieje")

                cur.execute(delete_query, (team_id,))

            conn.commit()

        return {
            "message": "Użytkownik został usunięty z zespołu projektu",
            "id": team_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))