"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await signIn("credentials", {
      username,
      password,
      redirect: false,
    });

    setLoading(false);

    if (result?.error) {
      setError("Usuário ou senha inválidos. Verifique suas credenciais corporativas.");
    } else {
      router.push("/");
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <img
            src="/logos/tanac-positivo-horizontal.png"
            alt="TANAC"
            style={{ height: 48, objectFit: "contain" }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          <div className="login-title">
            <span style={{ color: "var(--primary)", fontWeight: 700, fontSize: "1.5rem" }}>
              Tan
            </span>
            <span style={{ fontWeight: 700, fontSize: "1.5rem" }}>IA</span>
          </div>
          <p style={{ color: "var(--muted-foreground)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
            Plataforma de Agentes Inteligentes
          </p>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="field">
            <label htmlFor="username">Usuário corporativo</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="seu.usuario"
              required
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p style={{ color: "var(--muted-foreground)", fontSize: "0.75rem", textAlign: "center", marginTop: "1.5rem" }}>
          Use suas credenciais da rede TANAC
        </p>
      </div>

      <style jsx>{`
        .login-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--background);
          padding: 1rem;
        }
        .login-card {
          width: 100%;
          max-width: 400px;
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 2rem;
          box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        }
        .login-logo {
          text-align: center;
          margin-bottom: 2rem;
        }
        .login-title {
          margin-top: 0.75rem;
        }
        .login-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .field {
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }
        .field label {
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--foreground);
        }
        .field input {
          padding: 0.625rem 0.75rem;
          border: 1px solid var(--border);
          border-radius: var(--radius);
          background: var(--input);
          color: var(--foreground);
          font-size: 0.875rem;
          outline: none;
          transition: border-color 0.15s;
        }
        .field input:focus {
          border-color: var(--primary);
          box-shadow: 0 0 0 2px rgba(148, 193, 31, 0.2);
        }
        .btn-primary {
          padding: 0.625rem;
          background: var(--primary);
          color: var(--primary-foreground);
          border: none;
          border-radius: var(--radius);
          font-weight: 600;
          font-size: 0.875rem;
          cursor: pointer;
          transition: background 0.15s;
          margin-top: 0.5rem;
        }
        .btn-primary:hover:not(:disabled) {
          background: var(--primary-hover);
        }
        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .login-error {
          color: var(--destructive);
          font-size: 0.8125rem;
          padding: 0.5rem 0.75rem;
          background: rgba(220, 38, 38, 0.08);
          border-radius: var(--radius);
          border: 1px solid rgba(220, 38, 38, 0.2);
        }
      `}</style>
    </div>
  );
}
