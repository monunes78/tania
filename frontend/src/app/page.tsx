export default function Home() {
  return (
    <main
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        gap: "1rem",
      }}
    >
      <div style={{ fontSize: "3rem" }}>🤖</div>
      <h1 style={{ color: "var(--primary)", fontSize: "2rem", fontWeight: 700 }}>
        TanIA
      </h1>
      <p style={{ color: "var(--muted-foreground)" }}>
        Plataforma de Agentes Inteligentes TANAC
      </p>
    </main>
  );
}
