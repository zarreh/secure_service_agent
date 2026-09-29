"""Re-export of `zarreh_agentkit.api.middleware`.

Rejects an oversized request body at the ASGI layer with an honest 413
(OWASP LLM10, unbounded consumption): an attacker's payload never reaches routing.
"""

from zarreh_agentkit.api.middleware import MaxBodySizeMiddleware

__all__ = ["MaxBodySizeMiddleware"]
