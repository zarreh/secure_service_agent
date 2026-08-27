"""FastAPI application wiring (docs/PLAN.md).

Logging is configured once here. A correlation id is bound for the duration
of each request so every log line for one request is greppable by a single
id. A durable SQLite checkpointer (for the identity-gate + specialist graph)
and the PII-redaction logging hook are added in Phase 2/4 — the Phase 0
skeleton graph is stateless and needs neither.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from sentinel.api.middleware import MaxBodySizeMiddleware
from sentinel.api.rate_limit import limiter
from sentinel.api.routes import chat, health
from sentinel.observability import configure_logging
from sentinel.settings import get_settings

settings = get_settings()
configure_logging(settings.environment)

app = FastAPI(
    title="Secure Service Agent",
    description=(
        "Telecom customer support behind a full security envelope — input "
        "injection scanning, PIN-gated identity verification, and output "
        "leak/PII scanning, enforced in the graph, not the system prompt."
    ),
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(MaxBodySizeMiddleware, max_body_bytes=settings.max_request_body_bytes)


@app.middleware("http")
async def bind_correlation_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Binds a per-request correlation id into the structured-log context and
    echoes it back, so every log line for one request shares one id."""
    correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")
    response.headers["X-Correlation-ID"] = correlation_id
    return response


app.include_router(health.router)
app.include_router(chat.router)
