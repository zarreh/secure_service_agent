"""Single shared `Limiter`, applied per-route with `@limiter.limit(...)`.

Built on `zarreh_agentkit.api.rate_limit`. Applied per route rather than through
`SlowAPIMiddleware`, which treats `include_router` routes as exempt.
"""

from zarreh_agentkit.api.rate_limit import build_limiter, default_rate_limit

from secureagent.settings import get_settings

limiter = build_limiter()
DEFAULT_RATE_LIMIT = default_rate_limit(get_settings())
