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
    
@router.get("/tranag")
def get_tranag(
    search: str = Query(default="", max_length=100),
    gidnumer_kontrahenta: int | None = None
):
    search_like = f"%{search}%"

    query = """
        SELECT
            t.gidtyp,
            t.gidfirma,
            t.gidnumer,
            t.gidlp,
            t.numer,
            t.data,
            t.stan,
            t.typ,
            t.akronim_kontrahenta,
            t.nip_kontrahenta,
            t.gidnumer_kontrahenta
        FROM handlowe.tranag_from_public t
        WHERE 1=1
    """

    params = []

    if gidnumer_kontrahenta is not None:
        query += " AND t.gidnumer_kontrahenta = %s"
        params.append(gidnumer_kontrahenta)

    if search != "":
        query += """
            AND (
                CAST(t.gidnumer AS TEXT) ILIKE %s
                OR COALESCE(t.numer, '') ILIKE %s
                OR COALESCE(t.stan, '') ILIKE %s
                OR COALESCE(t.typ, '') ILIKE %s
                OR COALESCE(t.akronim_kontrahenta, '') ILIKE %s
                OR COALESCE(t.nip_kontrahenta, '') ILIKE %s
            )
        """
        params.extend([search_like, search_like, search_like, search_like, search_like, search_like])

    query += " ORDER BY t.gidnumer DESC LIMIT 100"

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


@router.get("/zamnag")
def get_zamnag(
    search: str = Query(default="", max_length=100),
    gidnumer_kontrahenta: int | None = None
):
    search_like = f"%{search}%"

    query = """
        SELECT
            z.gidtyp,
            z.gidfirma,
            z.gidnumer,
            z.gidlp,
            z.numer,
            z.data,
            z.stan,
            z.typ,
            z.akronim_kontrahenta,
            z.nip_kontrahenta,
            z.gidnumer_kontrahenta
        FROM handlowe.zamnag_from_public z
        WHERE 1=1
    """

    params = []

    if gidnumer_kontrahenta is not None:
        query += " AND z.gidnumer_kontrahenta = %s"
        params.append(gidnumer_kontrahenta)

    if search != "":
        query += """
            AND (
                CAST(z.gidnumer AS TEXT) ILIKE %s
                OR COALESCE(z.numer, '') ILIKE %s
                OR COALESCE(z.stan, '') ILIKE %s
                OR COALESCE(z.typ, '') ILIKE %s
                OR COALESCE(z.akronim_kontrahenta, '') ILIKE %s
                OR COALESCE(z.nip_kontrahenta, '') ILIKE %s
            )
        """
        params.extend([search_like, search_like, search_like, search_like, search_like, search_like])

    query += " ORDER BY z.gidnumer DESC LIMIT 100"

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