"""`MaxBodySizeMiddleware` is provided by `zarreh_agentkit.api.middleware`
(extracted substrate); this module re-exports it so `sentinel.api.middleware`
imports match the sibling apps' convention."""

from zarreh_agentkit.api.middleware import MaxBodySizeMiddleware

__all__ = ["MaxBodySizeMiddleware"]
