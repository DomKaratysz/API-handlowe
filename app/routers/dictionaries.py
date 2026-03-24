from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(tags=["dictionaries"])


@router.get("/project-statuses")
def get_project_statuses():
    query = """
        SELECT
            id,
            name,
            color,
            is_closed,
            is_active
        FROM handlowe.project_statuses
        WHERE COALESCE(is_active, true) = true
        ORDER BY id
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


@router.get("/project-stages")
def get_project_stages():
    query = """
        SELECT
            id,
            name,
            sort_order,
            is_closed,
            is_won,
            is_lost,
            is_active
        FROM handlowe.project_stages
        WHERE COALESCE(is_active, true) = true
        ORDER BY sort_order, id
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


@router.get("/project-types")
def get_project_types():
    query = """
        SELECT
            id,
            name,
            is_active
        FROM handlowe.project_types
        WHERE COALESCE(is_active, true) = true
        ORDER BY name
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