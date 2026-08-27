"""Phase 0 walking-skeleton request schema — replaced by a richer typed
request (customer id, message) once identity gating exists (Phase 2)."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
