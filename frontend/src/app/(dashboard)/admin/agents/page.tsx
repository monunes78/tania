"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Department {
  id: string;
  name: string;
}

interface Agent {
  id: string;
  name: string;
  description: string | null;
  system_prompt: string | null;
  temperature: string;
  max_context_chunks: number;
  enable_sql_access: boolean;
  is_active: boolean;
  department_id: string;
  department_name: string | null;
  llm_config_id: string | null;
  llm_config_name: string | null;
  qdrant_collection: string | null;
  document_count: number;
}

interface LLMConfig {
  id: string;
  name: string;
}

interface AgentForm {
  name: string;
  description: string;
  department_id: string;
  llm_config_id: string;
  temperature: string;
  max_context_chunks: number;
  enable_sql_access: boolean;
  is_active: boolean;
}

const emptyForm: AgentForm = {
  name: "",
  description: "",
  department_id: "",
  llm_config_id: "",
  temperature: "0.1",
  max_context_chunks: 5,
  enable_sql_access: false,
  is_active: true,
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [llmConfigs, setLLMConfigs] = useState<LLMConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterDept, setFilterDept] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Agent | null>(null);
  const [form, setForm] = useState<AgentForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [showPromptModal, setShowPromptModal] = useState(false);
  const [promptAgent, setPromptAgent] = useState<Agent | null>(null);
  const [promptText, setPromptText] = useState("");
  const [savingPrompt, setSavingPrompt] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [agentsData, deptsData, llmsData] = await Promise.all([
        apiFetch("/api/v1/agents" + (filterDept ? `?department_id=${filterDept}` : "")),
        apiFetch("/api/v1/departments"),
        apiFetch("/api/v1/admin/llm"),
      ]);
      setAgents(agentsData);
      setDepartments(deptsData);
      setLLMConfigs(llmsData);
    } catch {
      setError("Erro ao carregar dados.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filterDept]); // eslint-disable-line react-hooks/exhaustive-deps

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setShowModal(true);
  };

  const openEdit = (agent: Agent) => {
    setEditing(agent);
    setForm({
      name: agent.name,
      description: agent.description ?? "",
      department_id: agent.department_id,
      llm_config_id: agent.llm_config_id ?? "",
      temperature: agent.temperature,
      max_context_chunks: agent.max_context_chunks,
      enable_sql_access: agent.enable_sql_access,
      is_active: agent.is_active,
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
        llm_config_id: form.llm_config_id || null,
      };

      if (editing) {
        await apiFetch(`/api/v1/agents/${editing.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch("/api/v1/agents", {
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

  const handleDelete = async (agent: Agent) => {
    if (!confirm(`Excluir agente "${agent.name}"?`)) return;
    try {
      await apiFetch(`/api/v1/agents/${agent.id}`, { method: "DELETE" });
      await load();
    } catch {
      alert("Erro ao excluir agente.");
    }
  };

  const openPromptEditor = (agent: Agent) => {
    setPromptAgent(agent);
    setPromptText(agent.system_prompt ?? "");
    setShowPromptModal(true);
  };

  const handleSavePrompt = async () => {
    if (!promptAgent) return;
    setSavingPrompt(true);
    try {
      await apiFetch(`/api/v1/agents/${promptAgent.id}/prompt`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ system_prompt: promptText }),
      });
      setShowPromptModal(false);
      await load();
    } catch {
      alert("Erro ao salvar prompt.");
    } finally {
      setSavingPrompt(false);
    }
  };

  const filtered = filterDept
    ? agents.filter((a) => a.department_id === filterDept)
    : agents;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Agentes</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {filtered.length} agente(s)
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          + Novo Agente
        </button>
      </div>

      {/* Filtro por departamento */}
      <div className="mb-4">
        <select
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
          className="px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="">Todos os departamentos</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Agente</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Departamento</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">LLM</th>
                <th className="px-4 py-3 text-center font-medium text-muted-foreground">Docs</th>
                <th className="px-4 py-3 text-center font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((agent) => (
                <tr key={agent.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-foreground">{agent.name}</div>
                    {agent.description && (
                      <div className="text-xs text-muted-foreground truncate max-w-xs">{agent.description}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">{agent.department_name}</td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {agent.llm_config_name ?? <span className="italic">padrão</span>}
                  </td>
                  <td className="px-4 py-3 text-center text-muted-foreground">{agent.document_count}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                        agent.is_active
                          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {agent.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      onClick={() => openPromptEditor(agent)}
                      className="text-xs text-muted-foreground hover:text-foreground hover:underline"
                    >
                      Prompt
                    </button>
                    <button
                      onClick={() => openEdit(agent)}
                      className="text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(agent)}
                      className="text-xs text-destructive hover:underline"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Criar/Editar */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg border border-border shadow-xl w-full max-w-lg mx-4">
            <div className="px-6 py-4 border-b border-border">
              <h2 className="font-semibold text-foreground">
                {editing ? "Editar Agente" : "Novo Agente"}
              </h2>
            </div>

            <div className="px-6 py-4 space-y-4 max-h-[65vh] overflow-y-auto">
              {error && (
                <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">{error}</p>
              )}

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Nome *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Descrição</label>
                <input
                  type="text"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Departamento *</label>
                <select
                  value={form.department_id}
                  onChange={(e) => setForm((f) => ({ ...f, department_id: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="">Selecione...</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  LLM (opcional — usa o padrão se vazio)
                </label>
                <select
                  value={form.llm_config_id}
                  onChange={(e) => setForm((f) => ({ ...f, llm_config_id: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="">Usar LLM padrão</option>
                  {llmConfigs.map((l) => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Temperature</label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={form.temperature}
                    onChange={(e) => setForm((f) => ({ ...f, temperature: e.target.value }))}
                    className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Chunks RAG</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={form.max_context_chunks}
                    onChange={(e) => setForm((f) => ({ ...f, max_context_chunks: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.enable_sql_access}
                    onChange={(e) => setForm((f) => ({ ...f, enable_sql_access: e.target.checked }))}
                    className="rounded border-border accent-primary"
                  />
                  Acesso SQL
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
                disabled={saving || !form.name || !form.department_id}
                className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Prompt Editor */}
      {showPromptModal && promptAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg border border-border shadow-xl w-full max-w-2xl mx-4">
            <div className="px-6 py-4 border-b border-border">
              <h2 className="font-semibold text-foreground">
                System Prompt — {promptAgent.name}
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Instrução base do agente. O histórico de alterações é salvo automaticamente.
              </p>
            </div>

            <div className="px-6 py-4">
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                rows={14}
                placeholder="Ex: Você é um assistente especializado em RH da TANAC..."
                className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {promptText.length} caracteres
              </p>
            </div>

            <div className="px-6 py-4 border-t border-border flex justify-end gap-2">
              <button
                onClick={() => setShowPromptModal(false)}
                className="px-4 py-2 text-sm rounded-md border border-border text-foreground hover:bg-muted transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSavePrompt}
                disabled={savingPrompt}
                className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {savingPrompt ? "Salvando..." : "Salvar Prompt"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
