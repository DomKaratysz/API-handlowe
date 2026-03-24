from fastapi import APIRouter, HTTPException
from app.database import get_connection

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def get_users():
    query = """
        SELECT
            u.id,
            u.imie,
            u.nazwisko,
            u.email,
            u.telefon,
            u.stanowisko,
            u.przelozony_id,
            u.dzial,
            u.oddzial,
            u.is_admin,
            u.is_delete
        FROM crm.users u
        WHERE COALESCE(u.is_delete, false) = false
        ORDER BY u.nazwisko, u.imie
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