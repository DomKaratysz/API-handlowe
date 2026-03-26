from fastapi import HTTPException


def validate_project_data(cur, project, current_project_id=None):
    check_user_query = """
        SELECT id
        FROM crm.users
        WHERE id = %s
          AND COALESCE(is_delete, false) = false
    """

    check_status_query = """
        SELECT id
        FROM handlowe.project_statuses
        WHERE id = %s
          AND COALESCE(is_active, true) = true
    """

    check_stage_query = """
        SELECT
            id,
            COALESCE(is_closed, false) AS is_closed,
            COALESCE(is_won, false) AS is_won,
            COALESCE(is_lost, false) AS is_lost
        FROM handlowe.project_stages
        WHERE id = %s
          AND COALESCE(is_active, true) = true
    """

    check_project_type_query = """
        SELECT id
        FROM handlowe.project_types
        WHERE id = %s
          AND COALESCE(is_active, true) = true
    """

    check_project_number_query = """
        SELECT id
        FROM handlowe.projects
        WHERE project_number = %s
    """

    cur.execute(check_user_query, (project.owner_user_id,))
    owner = cur.fetchone()
    if not owner:
        raise HTTPException(status_code=400, detail="owner_user_id jest nieprawidłowy")

    if hasattr(project, "created_by") and project.created_by is not None:
        cur.execute(check_user_query, (project.created_by,))
        created_by_user = cur.fetchone()
        if not created_by_user:
            raise HTTPException(status_code=400, detail="created_by jest nieprawidłowy")

    if hasattr(project, "updated_by") and project.updated_by is not None:
        cur.execute(check_user_query, (project.updated_by,))
        updated_by_user = cur.fetchone()
        if not updated_by_user:
            raise HTTPException(status_code=400, detail="updated_by jest nieprawidłowy")

    cur.execute(check_status_query, (project.status_id,))
    status = cur.fetchone()
    if not status:
        raise HTTPException(status_code=400, detail="status_id jest nieprawidłowy")

    cur.execute(check_stage_query, (project.stage_id,))
    stage = cur.fetchone()
    if not stage:
        raise HTTPException(status_code=400, detail="stage_id jest nieprawidłowy")

    stage_id_db, stage_is_closed, stage_is_won, stage_is_lost = stage

    if stage_is_won and stage_is_lost:
        raise HTTPException(
            status_code=400,
            detail="Wybrany etap ma niespójne ustawienia: jednocześnie wygrany i przegrany"
        )

    if (stage_is_won or stage_is_lost) and not stage_is_closed:
        raise HTTPException(
            status_code=400,
            detail="Wybrany etap ma niespójne ustawienia: etap wygrany/przegrany musi być zamknięty"
        )

    actual_close_date = getattr(project, "actual_close_date", None)

    if stage_is_closed and actual_close_date is None:
        raise HTTPException(
            status_code=400,
            detail="Dla zamkniętego etapu actual_close_date jest wymagane"
        )

    if not stage_is_closed and actual_close_date is not None:
        raise HTTPException(
            status_code=400,
            detail="Dla otwartego etapu actual_close_date musi być puste"
        )

    if project.project_type_id is not None:
        cur.execute(check_project_type_query, (project.project_type_id,))
        project_type = cur.fetchone()
        if not project_type:
            raise HTTPException(status_code=400, detail="project_type_id jest nieprawidłowy")

    cur.execute(check_project_number_query, (project.project_number,))
    existing_project = cur.fetchone()

    if existing_project:
        existing_id = existing_project[0]
        if current_project_id is None:
            raise HTTPException(status_code=400, detail="project_number już istnieje")
        if existing_id != current_project_id:
            raise HTTPException(status_code=400, detail="project_number już istnieje w innym projekcie")