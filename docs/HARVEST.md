# Harvest log — patterns shared with A2 and A3

`docs/PLAN.md` §10. No shared package is extracted from a single implementation;
each pattern below is recorded as it recurs, and extraction happens as a discrete
step, driven by this list.

## Library gaps A4 hits on day one

| # | Gap | Effect here | Resolution |
|---|---|---|---|
| L1 | `stream_graph_events` in `zarreh-agentkit` v0.2.0 emits every `on_chain_end`, including the graph-level event and conditional-edge routing functions | `api/streaming.py` keeps a local copy with the `name == metadata["langgraph_node"]` filter | Fixed in library v0.2.1 (committed locally, not yet published). Drop the local copy once a tag exists |
| L2 | `configure_logging` has no processor hook (v0.2.0) | The redacting log processor (Phase 6) needs `extra_processors`, present in v0.2.1 | Same release; until then A4 wraps the library function locally, as A3 does |

## Extraction candidates

See `docs/PLAN.md` §10: scoped executor, node-level state projection, eval
metrics, redaction from a value set, tool-output injection scanner.
