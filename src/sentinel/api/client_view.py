"""What a client may see of a node's output (D-A4-11).

The stored event stream is the audit log, so it keeps every field, including a draft
the output guardrail went on to block. The client replay must not: a blocked draft
that is still readable in the network tab is not "discarded, not shown". So the
client view is an **allow-list**, not a deny-list: a field added to graph state later
is hidden until someone decides it is safe to show.
"""

from __future__ import annotations

_CLIENT_VISIBLE = frozenset(
    {
        "input_verdict",
        "identity",
        "route",
        "review",
        "citations",
        "output_verdict",
        "response",
    }
)


def project_for_client(output: object) -> object:
    if not isinstance(output, dict):
        return output
    return {key: value for key, value in output.items() if key in _CLIENT_VISIBLE}
