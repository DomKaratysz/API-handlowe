from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection

router = APIRouter(prefix="/project-stage-history", tags=["project-stage-history"])


@router.get("/")
def get_project_stage_history(project_id: int = Query(...)):
    query = """
        SELECT
            psh.id,
            psh.project_id,
            psh.old_stage_id,
            old_stage.name AS old_stage_name,
            psh.new_stage_id,
            new_stage.name AS new_stage_name,
            psh.changed_by_user_id,
            u.imie,
            u.nazwisko,
            psh.changed_at,
            psh.comment
        FROM handlowe.project_stage_history psh
        LEFT JOIN handlowe.project_stages old_stage
            ON psh.old_stage_id = old_stage.id
        LEFT JOIN handlowe.project_stages new_stage
            ON psh.new_stage_id = new_stage.id
        LEFT JOIN crm.users u
            ON psh.changed_by_user_id = u.id
        WHERE psh.project_id = %s
        ORDER BY psh.changed_at DESC, psh.id DESC
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