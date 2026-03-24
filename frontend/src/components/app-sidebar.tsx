"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface Agent {
  id: string;
  name: string;
}

interface Department {
  id: string;
  name: string;
  slug: string;
  icon: string;
  agents: Agent[];
}

interface SidebarProps {
  departments: Department[];
  isAdmin: boolean;
}

const ICONS: Record<string, string> = {
  users: "👥", briefcase: "💼", monitor: "🖥️", factory: "🏭",
  truck: "🚚", package: "📦", "bar-chart": "📊", "file-text": "📄",
  building: "🏢", handshake: "🤝", megaphone: "📢", heart: "❤️",
  wrench: "🔧", "tree-pine": "🌲", "dollar-sign": "💰", flask: "🧪",
  settings: "⚙️", shield: "🛡️", sprout: "🌱", scissors: "✂️",
  scale: "⚖️", layout: "📋",
};

export function AppSidebar({ departments, isAdmin }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      style={{
        width: collapsed ? "60px" : "var(--sidebar-width)",
        minHeight: "100vh",
        background: "var(--card)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        transition: "width 0.2s",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "1rem",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {!collapsed && (
          <span style={{ fontWeight: 700, color: "var(--primary)", fontSize: "1.1rem" }}>
            TanIA
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--muted-foreground)",
            fontSize: "1.2rem",
            padding: "0.25rem",
          }}
          title={collapsed ? "Expandir" : "Recolher"}
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Departamentos */}
      <nav style={{ flex: 1, overflowY: "auto", padding: "0.5rem 0" }}>
        {departments.map((dept) => (
          <div key={dept.id}>
            {dept.agents.map((agent) => {
              const href = `/chat/${agent.id}`;
              const active = pathname === href;
              return (
                <Link
                  key={agent.id}
                  href={href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.75rem",
                    padding: "0.5rem 1rem",
                    color: active ? "var(--primary)" : "var(--foreground)",
                    background: active ? "rgba(148,193,31,0.1)" : "transparent",
                    borderLeft: active ? "3px solid var(--primary)" : "3px solid transparent",
                    textDecoration: "none",
                    fontSize: "0.875rem",
                    transition: "background 0.15s",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                  }}
                  title={`${dept.name} — ${agent.name}`}
                >
                  <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>
                    {ICONS[dept.icon] ?? "🤖"}
                  </span>
                  {!collapsed && (
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                      {agent.name}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Admin link */}
      {isAdmin && !collapsed && (
        <div style={{ padding: "0.75rem 1rem", borderTop: "1px solid var(--border)" }}>
          <Link
            href="/admin"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              color: "var(--muted-foreground)",
              fontSize: "0.8125rem",
              textDecoration: "none",
            }}
          >
            ⚙️ <span>Admin Panel</span>
          </Link>
        </div>
      )}
    </aside>
  );
}
