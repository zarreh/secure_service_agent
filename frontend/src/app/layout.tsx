import type { Metadata } from "next";
import { PrototypeBanner } from "@/components/PrototypeBanner";
import "./globals.css";

export const metadata: Metadata = {
  title: "Secure Service Agent",
  description:
    "Telecom customer support behind a full security envelope — input injection scanning, PIN-gated identity verification, and output leak/PII scanning.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <PrototypeBanner />
        {children}
      </body>
    </html>
  );
}
