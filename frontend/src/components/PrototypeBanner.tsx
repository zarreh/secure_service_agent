import type { CSSProperties } from "react";

const REGULATORY_BASIS_URL =
  "https://github.com/zarreh/secure_service_agent/blob/main/NOTICE.md";

// The synthetic-data banner is on every page (docs/PLAN.md, second occurrence
// of this exact component shape after A3's — see docs/HARVEST.md F1): it
// renders in the root layout above all routes.
export function PrototypeBanner() {
  return (
    <div style={bannerStyle}>
      Architectural demonstration, fully synthetic accounts and PINs only —
      not connected to a real telecom account system. See{" "}
      <a href={REGULATORY_BASIS_URL} style={{ color: "inherit" }}>
        NOTICE
      </a>
      .
    </div>
  );
}

const bannerStyle: CSSProperties = {
  borderBottom: "1px solid #f0c36d",
  background: "#fff8e6",
  color: "#7a5b00",
  padding: "0.5rem 1rem",
  textAlign: "center",
  fontSize: "0.75rem",
};
