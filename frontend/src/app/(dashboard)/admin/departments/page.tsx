"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Department {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  is_active: boolean;
  agent_count: number;
  created_at: string;
}

interface DepartmentForm {
  name: string;
  slug: string;
  description: string;
  icon: string;
  is_active: boolean;
}

const emptyForm: DepartmentForm = {
  name: "",
  slug: "",
  description: "",
  icon: "users",
  is_active: true,
};

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [form, setForm] = useState<DepartmentForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/api/v1/departments");
      setDepartments(data);
    } catch {
      setError("Erro ao carregar departamentos.");
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

  const openEdit = (dept: Department) => {
    setEditing(dept);
    setForm({
      name: dept.name,
      slug: dept.slug,
      description: dept.description ?? "",
      icon: dept.icon ?? "users",
      is_active: dept.is_active,
    });
    setError("");
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      if (editing) {
        await apiFetch(`/api/v1/departments/${editing.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        });
      } else {
        await apiFetch("/api/v1/departments", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
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

  const handleDelete = async (dept: Department) => {
    if (!confirm(`Excluir departamento "${dept.name}"? Esta ação não pode ser desfeita.`)) return;
    try {
      await apiFetch(`/api/v1/departments/${dept.id}`, { method: "DELETE" });
      await load();
    } catch {
      alert("Erro ao excluir departamento.");
    }
  };

  const slugify = (text: string) =>
    text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Departamentos</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {departments.length} departamento(s) cadastrado(s)
          </p>
        </div>
        <button
          onClick={openCreate}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          + Novo Departamento
        </button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Nome</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Slug</th>
                <th className="px-4 py-3 text-center font-medium text-muted-foreground">Agentes</th>
                <th className="px-4 py-3 text-center font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {departments.map((dept) => (
                <tr key={dept.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3 font-medium text-foreground">{dept.name}</td>
                  <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{dept.slug}</td>
                  <td className="px-4 py-3 text-center text-muted-foreground">{dept.agent_count}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                        dept.is_active
                          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {dept.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      onClick={() => openEdit(dept)}
                      className="text-xs text-primary hover:underline"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(dept)}
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

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg border border-border shadow-xl w-full max-w-md mx-4">
            <div className="px-6 py-4 border-b border-border">
              <h2 className="font-semibold text-foreground">
                {editing ? "Editar Departamento" : "Novo Departamento"}
              </h2>
            </div>

            <div className="px-6 py-4 space-y-4">
              {error && (
                <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded">{error}</p>
              )}

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Nome *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => {
                    const name = e.target.value;
                    setForm((f) => ({
                      ...f,
                      name,
                      slug: editing ? f.slug : slugify(name),
                    }));
                  }}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Slug *</label>
                <input
                  type="text"
                  value={form.slug}
                  onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Descrição</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={form.is_active}
                  onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                  className="rounded border-border accent-primary"
                />
                <label htmlFor="is_active" className="text-sm text-foreground">
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
                disabled={saving || !form.name || !form.slug}
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
