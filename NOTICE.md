# NOTICE

## Independent implementation

This repository is an independent, clean-room implementation. The *problem
framing* — a telecom customer-support agent operating behind a full security
envelope (input scanning, identity-gated tool access, output leak scanning) —
was studied in graduate agentic-AI coursework. No course code, notebooks,
datasets or documents are reproduced or redistributed here.

Local source material used for reference during the build lives in
`reference/`, which is gitignored and never published.

## Data

All customer, plan, billing and network data is **synthetic**, generated or
adapted for this project. This repository contains no real customer records
and there is no configuration that points the application at a live carrier
system.

The policy knowledge base (`policy_kb`) is an illustrative telecom
support-policy document, not a real carrier's internal policy.

## Not a production support system

This is an architectural demonstration of a security-guardrailed agent
pattern. It is not connected to a real telecom account system, does not take
real billing actions, and is not a substitute for a carrier's own customer
support or fraud-prevention systems.
