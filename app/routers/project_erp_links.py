from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from app.schemas.project_erp_link import ProjectErpLinkCreate

router = APIRouter(prefix="/project-erp-links", tags=["project-erp-links"])


@router.get("/")
def get_project_erp_links(project_id: int = Query(...)):
    query = """
        SELECT
            pel.id,
            pel.project_id,
            pel.source_type,
            pel.gidtyp,
            pel.gidfirma,
            pel.gidnumer,
            pel.gidlp,
            pel.name,
            pel.add_time
        FROM handlowe.project_erp_links pel
        WHERE pel.project_id = %s
        ORDER BY pel.id DESC
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
def create_project_erp_link(link: ProjectErpLinkCreate):
    check_project_query = """
        SELECT id
        FROM handlowe.projects
        WHERE id = %s
    """

    check_duplicate_query = """
        SELECT id
        FROM handlowe.project_erp_links
        WHERE project_id = %s
          AND COALESCE(source_type, '') = COALESCE(%s, '')
          AND gidtyp = %s
          AND gidfirma = %s
          AND gidnumer = %s
          AND gidlp = %s
    """

    insert_query = """
        INSERT INTO handlowe.project_erp_links (
            project_id,
            source_type,
            gidtyp,
            gidfirma,
            gidnumer,
            gidlp,
            name,
            add_time
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_project_query, (link.project_id,))
                existing_project = cur.fetchone()
                if not existing_project:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                cur.execute(
                    check_duplicate_query,
                    (
                        link.project_id,
                        link.source_type,
                        link.gidtyp,
                        link.gidfirma,
                        link.gidnumer,
                        link.gidlp
                    )
                )
                existing_link = cur.fetchone()
                if existing_link:
                    raise HTTPException(status_code=400, detail="Ten link ERP jest już przypięty do projektu")

                cur.execute(
                    insert_query,
                    (
                        link.project_id,
                        link.source_type,
                        link.gidtyp,
                        link.gidfirma,
                        link.gidnumer,
                        link.gidlp,
                        link.name
                    )
                )
                new_id = cur.fetchone()[0]

            conn.commit()

        return {
            "message": "Link ERP został przypięty do projektu",
            "id": new_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{link_id}")
def delete_project_erp_link(link_id: int):
    check_query = """
        SELECT id
        FROM handlowe.project_erp_links
        WHERE id = %s
    """

    delete_query = """
        DELETE FROM handlowe.project_erp_links
        WHERE id = %s
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_query, (link_id,))
                existing = cur.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Link ERP nie istnieje")

                cur.execute(delete_query, (link_id,))

            conn.commit()

        return {
            "message": "Link ERP został usunięty",
            "id": link_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))