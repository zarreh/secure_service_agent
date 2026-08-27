"""Model selection per node — never inline in a node (docs/PLAN.md §9.3).

Empty until Phase 2/3 add real LLM-backed nodes. Will follow the two-profile
pattern carried across the portfolio: a cheap `fast` model for high-volume
classification (input/output scanners, supervisor routing) and a stronger
`reasoning` model for graded judgements (supervisor review).
"""
