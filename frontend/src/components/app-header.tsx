"use client";

import { signOut, useSession } from "next-auth/react";

export function AppHeader() {
  const { data: session } = useSession();

  return (
    <header
      style={{
        height: "56px",
        background: "var(--card)",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 1.5rem",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ color: "var(--primary)", fontWeight: 700 }}>Tan</span>
        <span style={{ fontWeight: 700 }}>IA</span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <span style={{ fontSize: "0.875rem", color: "var(--muted-foreground)" }}>
          {session?.user?.name}
        </span>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          style={{
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "0.375rem 0.75rem",
            fontSize: "0.8125rem",
            cursor: "pointer",
            color: "var(--foreground)",
          }}
        >
          Sair
        </button>
      </div>
    </header>
  );
}
