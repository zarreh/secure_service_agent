import type { ChatRunResponse } from "@/lib/types";

// Per-node cost accounting (docs/PLAN.md Phase 4). An unknown model prices to
// zero rather than inventing a figure, so a demo run can legitimately show $0.
export function CostMeter({ chat }: { chat: ChatRunResponse }) {
  return (
    <section aria-label="Cost" style={{ border: "1px solid #e5e5e5", borderRadius: "0.25rem", padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3 style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", color: "#737373", margin: 0 }}>
          Cost for this run
        </h3>
        <span style={{ fontFamily: "monospace", fontSize: "0.875rem" }}>
          ${chat.total_cost_usd.toFixed(4)}
        </span>
      </div>
      {chat.costs.length === 0 ? (
        <p style={{ fontSize: "0.75rem", color: "#737373" }}>
          No LLM cost recorded for this run — an unknown model prices to zero
          rather than inventing a figure.
        </p>
      ) : (
        <table style={{ width: "100%", fontSize: "0.75rem", marginTop: "0.5rem" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#737373" }}>
              <th style={{ fontWeight: 400 }}>Node</th>
              <th style={{ fontWeight: 400 }}>Model</th>
              <th style={{ fontWeight: 400 }}>Tokens</th>
              <th style={{ fontWeight: 400 }}>Cost</th>
            </tr>
          </thead>
          <tbody>
            {chat.costs.map((entry, i) => (
              <tr key={i}>
                <td style={{ fontFamily: "monospace" }}>{entry.node}</td>
                <td>{entry.model}</td>
                <td>{entry.prompt_tokens + entry.completion_tokens}</td>
                <td>${entry.cost_usd.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
