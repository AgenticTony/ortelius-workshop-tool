from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.rate_limit import limiter
from app.routes import sessions, ideas, analysis, stream
from app.services.event_bus import event_bus


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Capture the running event loop so sync route handlers can publish SSE
    events via call_soon_threadsafe (they run in threadpool threads)."""
    event_bus.set_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="Workshop Tool API", version="0.1.0", lifespan=lifespan)

# ── Rate limiting ─────────────────────────────────────────────
# In-memory store (single instance). Protects Claude cost (/analyse) and
# guards against idea spam during a workshop. Multi-instance deployment
# would need a shared backend (redis) — out of scope for the prototype.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(ideas.router)
app.include_router(analysis.router)
app.include_router(stream.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "workshop-tool"}
