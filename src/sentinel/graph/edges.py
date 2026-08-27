"""Routing predicates — one small function each (docs/PLAN.md §9.3).

Empty until Phase 2/3 add the real routing: `route_after_guardrail` (blocked
vs. allow), `route_supervisor_to_agent` (network/billing/account/escalation),
`route_after_review` (publish vs. re-route), `route_after_output_guardrail`
(respond vs. block), mirroring the node names confirmed against
`reference/telecom_chatbot_app.py`.
"""
