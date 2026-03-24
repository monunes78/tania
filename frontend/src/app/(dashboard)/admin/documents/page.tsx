"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Agent {
  id: string;
  name: string;
  department_name: string | null;
}

interface Document {
  id: string;
  original_name: string;
  file_type: string;
  classification: string;
  version: number;
  status: string;
  error_message: string | null;
  file_size_bytes: number | null;
  chunk_count: number;
  indexed_at: string | null;
  created_at: string;
  uploaded_by_name: string | null;
}

const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  pending:    { label: "Aguardando",  cls: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" },
  processing: { label: "Processando", cls: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
  indexed:    { label: "Indexado",    cls: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
  error:      { label: "Erro",        cls: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
  expired:    { label: "Expirado",    cls: "bg-muted text-muted-foreground" },
};

function fmtBytes(b: number | null) {
  if (!b) return "—";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [classification, setClassification] = useState("public");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState("");
  const [pollTimer, setPollTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    apiFetch<Agent[]>("/api/v1/agents").then(setAgents).catch(() => {});
  }, []);

  const loadDocs = async (agentId: string) => {
    if (!agentId) return;
    setLoading(true);
    try {
      const data = await apiFetch<Document[]>(`/api/v1/documents/${agentId}`);
      setDocuments(data);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAgent) loadDocs(selectedAgent);
    else setDocuments([]);
  }, [selectedAgent]); // eslint-disable-line react-hooks/exhaustive-deps

  // Polling enquanto há docs processando
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "pending" || d.status === "processing");
    if (hasProcessing && selectedAgent) {
      const t = setTimeout(() => loadDocs(selectedAgent), 3000);
      setPollTimer(t);
    }
    return () => {
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [documents]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !selectedAgent) return;
    setUploadError("");
    setUploading(true);

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";

    for (const file of Array.from(files)) {
      const form = new FormData();
      form.append("file", file);
      form.append("classification", classification);

      try {
        const res = await fetch(`${apiBase}/api/v1/documents/${selectedAgent}`, {
          method: "POST",
          credentials: "include",
          body: form,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Erro no upload" }));
          setUploadError(err.detail);
        }
      } catch {
        setUploadError(`Erro ao enviar ${file.name}`);
      }
    }

    setUploading(false);
    await loadDocs(selectedAgent);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleReindex = async (docId: string) => {
    try {
      await apiFetch(`/api/v1/documents/${selectedAgent}/${docId}/reindex`, { method: "POST" });
      await loadDocs(selectedAgent);
    } catch {
      alert("Erro ao re-indexar.");
    }
  };

  const handleDelete = async (doc: Document) => {
    if (!confirm(`Excluir "${doc.original_name}"? Os vetores serão removidos do Qdrant.`)) return;
    try {
      await apiFetch(`/api/v1/documents/${selectedAgent}/${doc.id}`, { method: "DELETE" });
      await loadDocs(selectedAgent);
    } catch {
      alert("Erro ao excluir documento.");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    handleUpload(e.dataTransfer.files);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Base de Conhecimento</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Faça upload de documentos para cada agente
        </p>
      </div>

      {/* Seletor de agente */}
      <div className="mb-6">
        <select
          value={selectedAgent}
          onChange={(e) => setSelectedAgent(e.target.value)}
          className="px-3 py-2 rounded-md border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-w-64"
        >
          <option value="">Selecione um agente...</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.department_name ? `${a.department_name} — ` : ""}{a.name}
            </option>
          ))}
        </select>
      </div>

      {selectedAgent && (
        <>
          {/* Upload zone */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="mb-6 border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/50 transition-colors"
          >
            <p className="text-sm text-muted-foreground mb-3">
              Arraste arquivos aqui ou clique para selecionar
              <br />
              <span className="text-xs">PDF, DOCX, XLSX, TXT · máximo 50 MB por arquivo</span>
            </p>

            <div className="flex items-center justify-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <label className="text-xs text-foreground">Classificação:</label>
                <select
                  value={classification}
                  onChange={(e) => setClassification(e.target.value)}
                  className="text-xs px-2 py-1 rounded border border-border bg-background text-foreground focus:outline-none"
                >
                  <option value="public">Público</option>
                  <option value="confidential">Confidencial</option>
                </select>
              </div>

              <label className={`px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors ${
                uploading
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : "bg-primary text-primary-foreground hover:bg-primary/90"
              }`}>
                {uploading ? "Enviando..." : "Selecionar arquivos"}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.xlsx,.txt"
                  className="hidden"
                  disabled={uploading}
                  onChange={(e) => handleUpload(e.target.files)}
                />
              </label>
            </div>

            {uploadError && (
              <p className="mt-2 text-sm text-destructive">{uploadError}</p>
            )}
          </div>

          {/* Lista de documentos */}
          {loading ? (
            <p className="text-muted-foreground text-sm">Carregando...</p>
          ) : documents.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-border rounded-lg">
              <p className="text-muted-foreground text-sm">
                Nenhum documento neste agente ainda.
              </p>
            </div>
          ) : (
            <div className="rounded-lg border border-border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Arquivo</th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">Tipo</th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">Classificação</th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">Chunks</th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">Tamanho</th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {documents.map((doc) => {
                    const s = STATUS_LABELS[doc.status] ?? { label: doc.status, cls: "bg-muted text-muted-foreground" };
                    return (
                      <tr key={doc.id} className="hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-medium text-foreground truncate max-w-xs">{doc.original_name}</div>
                          {doc.error_message && (
                            <div className="text-xs text-destructive truncate max-w-xs" title={doc.error_message}>
                              {doc.error_message}
                            </div>
                          )}
                          {doc.version > 1 && (
                            <span className="text-xs text-muted-foreground">v{doc.version}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="font-mono text-xs uppercase text-muted-foreground">{doc.file_type}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            doc.classification === "confidential"
                              ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
                              : "bg-muted text-muted-foreground"
                          }`}>
                            {doc.classification === "confidential" ? "Confidencial" : "Público"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center text-muted-foreground">
                          {doc.status === "indexed" ? doc.chunk_count : "—"}
                        </td>
                        <td className="px-4 py-3 text-center text-muted-foreground text-xs">
                          {fmtBytes(doc.file_size_bytes)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${s.cls}`}>
                            {s.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          {(doc.status === "error" || doc.status === "indexed") && (
                            <button
                              onClick={() => handleReindex(doc.id)}
                              className="text-xs text-muted-foreground hover:text-foreground hover:underline"
                            >
                              Re-indexar
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(doc)}
                            className="text-xs text-destructive hover:underline"
                          >
                            Excluir
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
