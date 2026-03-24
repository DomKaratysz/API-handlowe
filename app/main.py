from fastapi import FastAPI, HTTPException
from app.routers import projects, tasks, users
from app.database import get_connection

app = FastAPI(title="API handlowe")

app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {"message": "API handlowe działa"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                row = cur.fetchone()
        return {"status": "ok", "result": row[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))