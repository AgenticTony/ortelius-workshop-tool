import logging
import uuid
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.errors import WorkshopError, AuthenticationError
from app.rate_limit import limiter
from app.routes import sessions, ideas, analysis, stream
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


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


# ── Request-id middleware ─────────────────────────────────────
class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign a per-request id, attach it to logs + the X-Request-ID header.

    Lets a user-facing error be correlated to the server logs without leaking
    internals. If the client sent X-Request-ID, reuse it; else generate one.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIdMiddleware)


# ── Error handlers ────────────────────────────────────────────


@app.exception_handler(WorkshopError)
async def workshop_error_handler(request: Request, exc: WorkshopError):
    """Typed workshop errors → {detail, code} with the error's status code."""
    headers = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """Catch-all: never leak a stack trace. Log with request_id, return 500."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled error [request_id=%s]", request_id)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "internal_error",
            "request_id": request_id,
        },
    )


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
