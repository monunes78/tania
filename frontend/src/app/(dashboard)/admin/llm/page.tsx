"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface LLMConfig {
  id: string;
  name: string;
  provider: string;
  model_name: string;
  api_base_url: string | null;
  is_default: boolean;
  is_active: boolean;
  has_api_key: boolean;
  created_at: string;
}

interface LLMForm {
  name: string;
  provider: string;
  model_name: string;
  api_key: string;
  api_base_url: string;
  is_default: boolean;
  is_active: boolean;
}

const emptyForm: LLMForm = {
  name: "",
  provider: "openrouter",
  model_name: "",
  api_key: "",
  api_base_url: "",
  is_default: false,
  is_active: true,
};

const PROVIDERS = ["openrouter", "openai", "anthropic", "ollama", "azure"];

export default function LLMConfigPage() {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<LLMConfig | null>(null);
  const [form, setForm] = useState<LLMForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; latency_ms: number; error?: string }>>({});
  const [testing, setTesting] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/admin/llm");
      setConfigs(data);
    } catch {
      setError("Erro ao carregar configurações LLM.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setShowModal(true);
  };

  const openEdit = (config: LLMConfig) => {
    setEditing(config);
    setForm({
      name: config.name,
      provider: config.provider,
      model_name: config.model_name,
      api_key: "",
      api_base_url: config.api_base_url ?? "",
      is_default: config.is_default,
      is_active: config.is_active,
    });
    setError("");
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...form,
        api_key: form.api_key || undefined,
        api_base_url: form.api_base_url || undefined,
      };

      if (editing) {
        await apiFetch(`/api/v1/admin/llm/${editing.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch("/api/v1/admin/llm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }
      setShowModal(false);
      await load();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro ao salvar.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (config: LLMConfig) => {
    if (config.is_default) {
      alert("Não é possível excluir a configuração padrão.");
      return;
    }
    if (!confirm(`Excluir "${config.name}"?`)) return;
    try {
      await apiFetch(`/api/v1/admin/llm/${config.id}`, { method: "DELETE" });
      await load();
    } catch {
      alert("Erro ao excluir configuração.");
    }
  };

  const handleTest = async (configId: string) => {
    setTesting(configId);
    try {
      const result = await apiFetch(`/api/v1/admin/llm/${configId}/test`, { method: "POST" });
      setTestResults((r) => ({ ...r, [configId]: result }));
    } catch {
      setTestResults((r) => ({ ...r, [configId]: { success: false, latency_ms: 0, error: "Erro na requisição" } }));
    } finally {
      setTesting(null);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Configurações LLM</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Gerencie provedores e modelos de linguagem
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          + Nova Configuração
        </button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : configs.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-border rounded-lg">
          <p className="text-muted-foreground">Nenhuma configuração LLM cadastrada.</p>
          <p className="text-sm text-muted-foreground mt-1">
            Adicione um provedor para começar a usar os agentes.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map((config) => {
            const testResult = testResults[config.id];
            return (
              <div
                key={config.id}
                className="rounded-lg border border-border bg-card p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-foreground">{config.name}</h3>
                      {config.is_default && (
                        <span className="px-2 py-0.5 rounded-full text-xs bg-primary/15 text-primary font-medium">
                          Padrão
                        </span>
                      )}
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          config.is_active
                            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {config.is_active ? "Ativo" : "Inativo"}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      <span className="font-mono">{config.provider}</span>
                      {" · "}
                      <span className="font-mono">{config.model_name}</span>
                      {config.has_api_key && (
                        <span className="ml-2 text-xs text-muted-foreground">🔑 API key configurada</span>
                      )}
                    </p>
                    {testResult && (
                      <p
                        className={`text-xs mt-1 ${
                          testResult.success ? "text-green-600 dark:text-green-400" : "text-destructive"
                        }`}
                      >
                        {testResult.success
                          ? `✓ Conexão OK — ${testResult.latency_ms}ms`
                          : `✗ ${testResult.error}`}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleTest(config.id)}
                      disabled={testing === config.id}
                      className="text-xs px-3 py-1 rounded border border-border text-foreground hover:bg-muted transition-colors disabled:opacity-50"
                    >
                      {testing === config.id ? "Testando..." : "Testar"}
                    </button>
                    <button
                      onClick={() => openEdit(config)}
                      className="text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(config)}
                      className="text-xs text-destructive hover:underline"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg border border-border shadow-xl w-full max-w-md mx-4">
            <div className="px-6 py-4 border-b border-border">
              <h2 className="font-semibold text-foreground">
                {editing ? "Editar Configuração LLM" : "Nova Configuração LLM"}
              </h2>
            </div>

            <div className="px-6 py-4 space-y-4 max-h-[70vh] overflow-y-auto">
              {error && (
                <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">{error}</p>
              )}

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Nome *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="ex: OpenRouter Principal"
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Provedor *</label>
                <select
                  value={form.provider}
                  onChange={(e) => setForm((f) => ({ ...f, provider: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {PROVIDERS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Modelo *
                </label>
                <input
                  type="text"
                  value={form.model_name}
                  onChange={(e) => setForm((f) => ({ ...f, model_name: e.target.value }))}
                  placeholder="ex: anthropic/claude-3-5-sonnet"
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  API Key {editing && "(deixe vazio para manter a atual)"}
                </label>
                <input
                  type="password"
                  value={form.api_key}
                  onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
                  placeholder={editing ? "••••••••" : "sk-or-..."}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  API Base URL (opcional)
                </label>
                <input
                  type="text"
                  value={form.api_base_url}
                  onChange={(e) => setForm((f) => ({ ...f, api_base_url: e.target.value }))}
                  placeholder="ex: http://localhost:11434 (Ollama)"
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_default}
                    onChange={(e) => setForm((f) => ({ ...f, is_default: e.target.checked }))}
                    className="rounded border-border accent-primary"
                  />
                  Padrão
                </label>
                <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                    className="rounded border-border accent-primary"
                  />
                  Ativo
                </label>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-border flex justify-end gap-2">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm rounded-md border border-border text-foreground hover:bg-muted transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.name || !form.provider || !form.model_name}
                className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
