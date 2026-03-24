import { auth } from "@/lib/auth";

export default async function DashboardPage() {
  const session = await auth();
  const user = session?.user as any;

  return (
    <div>
      <h1
        style={{
          fontSize: "1.5rem",
          fontWeight: 700,
          marginBottom: "0.5rem",
        }}
      >
        Olá, {user?.name?.split(" ")[0] ?? "usuário"} 👋
      </h1>
      <p style={{ color: "var(--muted-foreground)", marginBottom: "2rem" }}>
        Selecione um agente na barra lateral para iniciar uma conversa.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: "1rem",
          maxWidth: "900px",
        }}
      >
        {/* Cards de departamentos — serão populados via API */}
        <div
          style={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "1.25rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.5rem",
          }}
        >
          <span style={{ fontSize: "2rem" }}>🤖</span>
          <p style={{ fontSize: "0.875rem", color: "var(--muted-foreground)" }}>
            Nenhum agente disponível ainda. Configure departamentos e agentes no Admin Panel.
          </p>
        </div>
      </div>
    </div>
  );
}
