from fastapi import FastAPI
from app.routers import projects, tasks

app = FastAPI(title="API handlowe")

app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    return {"message": "API handlowe działa"}


@app.get("/health")
def health():
    return {"status": "ok"}