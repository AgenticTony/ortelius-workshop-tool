from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import sessions, ideas, analysis

app = FastAPI(title="Workshop Tool API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(ideas.router)
app.include_router(analysis.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "workshop-tool"}
