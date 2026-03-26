from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from app.schemas.project import ProjectCreate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.project_archive import ProjectArchiveAction
from app.utils.project_validation import validate_project_data

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
def get_projects(
    search: str = Query(default="", max_length=100),
    status_id: int | None = None,
    stage_id: int | None = None,
    owner_user_id: int | None = None,
    is_archived: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="id"),
    sort_dir: str = Query(default="desc")
):
    allowed_sort_columns = {
        "id": "p.id",
        "project_number": "p.project_number",
        "name": "p.name",
        "planned_close_date": "p.planned_close_date",
        "estimated_value_net": "p.estimated_value_net",
        "created_at": "p.created_at",
        "updated_at": "p.updated_at"
    }

    allowed_sort_directions = {"asc", "desc"}

    if sort_by not in allowed_sort_columns:
        raise HTTPException(status_code=400, detail="Nieprawidłowe pole sortowania")

    if sort_dir.lower() not in allowed_sort_directions:
        raise HTTPException(status_code=400, detail="Nieprawidłowy kierunek sortowania")

    order_by_column = allowed_sort_columns[sort_by]
    order_by_direction = sort_dir.upper()

    base_from = """
        FROM handlowe.projects p
        LEFT JOIN crm.users u
            ON p.owner_user_id = u.id
        LEFT JOIN handlowe.project_types pt
            ON p.project_type_id = pt.id
        LEFT JOIN handlowe.project_statuses ps
            ON p.status_id = ps.id
        LEFT JOIN handlowe.project_stages pg
            ON p.stage_id = pg.id
        WHERE 1=1
    """

    params = []

    if search != "":
        base_from += """
            AND (
                COALESCE(p.project_number, '') ILIKE %s
                OR COALESCE(p.name, '') ILIKE %s
            )
        """
        search_like = f"%{search}%"
        params.extend([search_like, search_like])

    if status_id is not None:
        base_from += " AND p.status_id = %s"
        params.append(status_id)

    if stage_id is not None:
        base_from += " AND p.stage_id = %s"
        params.append(stage_id)

    if owner_user_id is not None:
        base_from += " AND p.owner_user_id = %s"
        params.append(owner_user_id)

    if is_archived is not None:
        base_from += " AND p.is_archived = %s"
        params.append(is_archived)

    data_query = f"""
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
        {base_from}
        ORDER BY {order_by_column} {order_by_direction}, p.id DESC
        LIMIT %s OFFSET %s
    """

    count_query = f"""
        SELECT COUNT(*)
        {base_from}
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_query, params)
                total = cur.fetchone()[0]

                data_params = params.copy()
                data_params.extend([limit, offset])

                cur.execute(data_query, data_params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        items = [dict(zip(columns, row)) for row in rows]

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_dir": sort_dir.lower()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_project_stats(user_id: int | None = None):
    total_query = """
        SELECT COUNT(*)
        FROM handlowe.projects
    """

    active_query = """
        SELECT COUNT(*)
        FROM handlowe.projects
        WHERE COALESCE(is_archived, false) = false
    """

    archived_query = """
        SELECT COUNT(*)
        FROM handlowe.projects
        WHERE COALESCE(is_archived, false) = true
    """

    my_query = """
        SELECT COUNT(*)
        FROM handlowe.projects
        WHERE owner_user_id = %s
    """

    status_query = """
        SELECT
            ps.id,
            ps.name,
            COUNT(p.id) AS count
        FROM handlowe.project_statuses ps
        LEFT JOIN handlowe.projects p
            ON p.status_id = ps.id
        GROUP BY ps.id, ps.name
        ORDER BY ps.id
    """

    stage_query = """
        SELECT
            pg.id,
            pg.name,
            COUNT(p.id) AS count
        FROM handlowe.project_stages pg
        LEFT JOIN handlowe.projects p
            ON p.stage_id = pg.id
        GROUP BY pg.id, pg.name
        ORDER BY pg.sort_order, pg.id
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(total_query)
                total_projects = cur.fetchone()[0]

                cur.execute(active_query)
                active_projects = cur.fetchone()[0]

                cur.execute(archived_query)
                archived_projects = cur.fetchone()[0]

                my_projects = None
                if user_id is not None:
                    cur.execute(my_query, (user_id,))
                    my_projects = cur.fetchone()[0]

                cur.execute(status_query)
                status_rows = cur.fetchall()
                status_columns = [desc[0] for desc in cur.description]
                by_status = [dict(zip(status_columns, row)) for row in status_rows]

                cur.execute(stage_query)
                stage_rows = cur.fetchall()
                stage_columns = [desc[0] for desc in cur.description]
                by_stage = [dict(zip(stage_columns, row)) for row in stage_rows]

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "archived_projects": archived_projects,
            "my_projects": my_projects,
            "by_status": by_status,
            "by_stage": by_stage
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my")
def get_my_projects(
    user_id: int = Query(...),
    search: str = Query(default="", max_length=100),
    status_id: int | None = None,
    stage_id: int | None = None,
    is_archived: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="id"),
    sort_dir: str = Query(default="desc")
):
    allowed_sort_columns = {
        "id": "p.id",
        "project_number": "p.project_number",
        "name": "p.name",
        "planned_close_date": "p.planned_close_date",
        "estimated_value_net": "p.estimated_value_net",
        "created_at": "p.created_at",
        "updated_at": "p.updated_at"
    }

    allowed_sort_directions = {"asc", "desc"}

    if sort_by not in allowed_sort_columns:
        raise HTTPException(status_code=400, detail="Nieprawidłowe pole sortowania")

    if sort_dir.lower() not in allowed_sort_directions:
        raise HTTPException(status_code=400, detail="Nieprawidłowy kierunek sortowania")

    order_by_column = allowed_sort_columns[sort_by]
    order_by_direction = sort_dir.upper()

    base_from = """
        FROM handlowe.projects p
        LEFT JOIN crm.users u
            ON p.owner_user_id = u.id
        LEFT JOIN handlowe.project_types pt
            ON p.project_type_id = pt.id
        LEFT JOIN handlowe.project_statuses ps
            ON p.status_id = ps.id
        LEFT JOIN handlowe.project_stages pg
            ON p.stage_id = pg.id
        WHERE p.owner_user_id = %s
    """

    params = [user_id]

    if search != "":
        base_from += """
            AND (
                COALESCE(p.project_number, '') ILIKE %s
                OR COALESCE(p.name, '') ILIKE %s
            )
        """
        search_like = f"%{search}%"
        params.extend([search_like, search_like])

    if status_id is not None:
        base_from += " AND p.status_id = %s"
        params.append(status_id)

    if stage_id is not None:
        base_from += " AND p.stage_id = %s"
        params.append(stage_id)

    if is_archived is not None:
        base_from += " AND p.is_archived = %s"
        params.append(is_archived)

    data_query = f"""
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
        {base_from}
        ORDER BY {order_by_column} {order_by_direction}, p.id DESC
        LIMIT %s OFFSET %s
    """

    count_query = f"""
        SELECT COUNT(*)
        {base_from}
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_query, params)
                total = cur.fetchone()[0]

                data_params = params.copy()
                data_params.extend([limit, offset])

                cur.execute(data_query, data_params)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        items = [dict(zip(columns, row)) for row in rows]

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_dir": sort_dir.lower(),
            "user_id": user_id
        }

    except HTTPException:
        raise
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

@router.get("/{project_id}/full")
def get_project_full(project_id: int):
    project_query = """
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

    team_query = """
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

    task_links_query = """
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

    erp_links_query = """
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
                cur.execute(project_query, (project_id,))
                project_row = cur.fetchone()

                if not project_row:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                project_columns = [desc[0] for desc in cur.description]
                project_item = dict(zip(project_columns, project_row))

                cur.execute(team_query, (project_id,))
                team_rows = cur.fetchall()
                team_columns = [desc[0] for desc in cur.description]
                team_items = [dict(zip(team_columns, row)) for row in team_rows]

                cur.execute(task_links_query, (project_id,))
                task_rows = cur.fetchall()
                task_columns = [desc[0] for desc in cur.description]
                task_items = [dict(zip(task_columns, row)) for row in task_rows]

                cur.execute(erp_links_query, (project_id,))
                erp_rows = cur.fetchall()
                erp_columns = [desc[0] for desc in cur.description]
                erp_items = [dict(zip(erp_columns, row)) for row in erp_rows]

        return {
            "project": project_item,
            "team": team_items,
            "task_links": task_items,
            "erp_links": erp_items
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            actual_close_date,
            description,
            internal_notes,
            created_by,
            created_at,
            is_archived
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
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
        project.actual_close_date,
        project.description,
        project.internal_notes,
        project.created_by
    )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                validate_project_data(cur, project)

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
    get_existing_query = """
        SELECT id, stage_id
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

    insert_stage_history_query = """
        INSERT INTO handlowe.project_stage_history (
            project_id,
            old_stage_id,
            new_stage_id,
            changed_by_user_id,
            changed_at,
            comment
        )
        VALUES (%s, %s, %s, %s, NOW(), %s)
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(get_existing_query, (project_id,))
                existing = cur.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Projekt nie istnieje")

                old_stage_id = existing[1]

                validate_project_data(cur, project, current_project_id=project_id)

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

                if old_stage_id != project.stage_id:
                    cur.execute(
                        insert_stage_history_query,
                        (
                            project_id,
                            old_stage_id,
                            project.stage_id,
                            project.updated_by,
                            f"Automatyczna zmiana etapu z API: {old_stage_id} -> {project.stage_id}"
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
    
@router.patch("/{project_id}/archive")
def archive_project(project_id: int, payload: ProjectArchiveAction):
    check_query = """
        SELECT id
        FROM handlowe.projects
        WHERE id = %s
    """

    update_query = """
        UPDATE handlowe.projects
        SET
            is_archived = true,
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

                cur.execute(update_query, (payload.updated_by, project_id))
            conn.commit()

        return {
            "message": "Projekt został zarchiwizowany",
            "id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}/unarchive")
def unarchive_project(project_id: int, payload: ProjectArchiveAction):
    check_query = """
        SELECT id
        FROM handlowe.projects
        WHERE id = %s
    """

    update_query = """
        UPDATE handlowe.projects
        SET
            is_archived = false,
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

                cur.execute(update_query, (payload.updated_by, project_id))
            conn.commit()

        return {
            "message": "Projekt został przywrócony z archiwum",
            "id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))