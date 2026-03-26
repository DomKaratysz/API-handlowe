from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection

router = APIRouter(prefix="/erp", tags=["erp"])


@router.get("/kntkarty")
def get_kntkarty(search: str = Query(default="", max_length=100)):
    query = """
        SELECT
            k.gidnumer,
            k.gidtyp,
            k.gidfirma,
            k.gidlp,
            k.akronim,
            k.nip,
            k.nazwa,
            k.adres
        FROM handlowe.kntkarty_from_public k
        WHERE (
            %s = ''
            OR CAST(k.gidnumer AS TEXT) ILIKE %s
            OR COALESCE(k.akronim, '') ILIKE %s
            OR COALESCE(k.nip, '') ILIKE %s
            OR COALESCE(k.nazwa, '') ILIKE %s
        )
        ORDER BY k.nazwa
        LIMIT 100
    """

    search_like = f"%{search}%"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (search, search_like, search_like, search_like, search_like)
                )
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        items = [dict(zip(columns, row)) for row in rows]
        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kntosoby")
def get_kntosoby(
    search: str = Query(default="", max_length=100),
    gidnumer: int | None = None
):
    search_like = f"%{search}%"

    query = """
        SELECT
            o.gidtyp,
            o.gidfirma,
            o.gidnumer,
            o.gidlp,
            o.nazwa,
            o.email,
            o.telefon,
            o.firma
        FROM handlowe.kntosoby_from_public o
        WHERE 1=1
    """

    params = []

    if gidnumer is not None:
        query += " AND o.gidnumer = %s"
        params.append(gidnumer)

    if search != "":
        query += """
            AND (
                COALESCE(o.nazwa, '') ILIKE %s
                OR COALESCE(o.email, '') ILIKE %s
                OR COALESCE(o.telefon, '') ILIKE %s
                OR COALESCE(o.firma, '') ILIKE %s
            )
        """
        params.extend([search_like, search_like, search_like, search_like])

    query += " ORDER BY o.nazwa LIMIT 100"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        items = [dict(zip(columns, row)) for row in rows]
        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))