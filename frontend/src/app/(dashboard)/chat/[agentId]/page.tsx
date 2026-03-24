"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || streaming) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: text },
    ]);
    setStreaming(true);
    setStreamingContent("");

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";

    try {
      const res = await fetch(`${apiBase}/api/v1/chat/stream`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: agentId,
          message: text,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro na requisição" }));
        throw new Error(err.detail);
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.token) {
              accumulated += data.token;
              setStreamingContent(accumulated);
            }
            if (data.done) {
              setMessages((prev) => [
                ...prev,
                { id: data.message_id, role: "assistant", content: accumulated },
              ]);
              setStreamingContent("");
              if (!conversationId) {
                // Extract conversation_id from next request — not available here,
                // so we'll fetch conversations after first message
              }
            }
            if (data.error) {
              throw new Error(data.error);
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro desconhecido";
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `⚠️ ${msg}`,
        },
      ]);
      setStreamingContent("");
    } finally {
      setStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
    setStreamingContent("");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 4rem)",
        maxWidth: "800px",
        margin: "0 auto",
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: "0.75rem",
        }}
      >
        <button
          onClick={newConversation}
          style={{
            fontSize: "0.8125rem",
            color: "var(--muted-foreground)",
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: "0.375rem",
            padding: "0.25rem 0.75rem",
            cursor: "pointer",
          }}
        >
          + Nova conversa
        </button>
      </div>

      {/* Mensagens */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          paddingBottom: "1rem",
        }}
      >
        {messages.length === 0 && !streamingContent && (
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--muted-foreground)",
              fontSize: "0.9375rem",
            }}
          >
            Olá! Como posso ajudar?
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              style={{
                maxWidth: "75%",
                padding: "0.75rem 1rem",
                borderRadius: "0.75rem",
                fontSize: "0.9375rem",
                lineHeight: "1.6",
                background:
                  msg.role === "user"
                    ? "var(--primary)"
                    : "var(--card)",
                color:
                  msg.role === "user"
                    ? "var(--primary-foreground)"
                    : "var(--foreground)",
                border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Streaming */}
        {streamingContent && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div
              style={{
                maxWidth: "75%",
                padding: "0.75rem 1rem",
                borderRadius: "0.75rem",
                fontSize: "0.9375rem",
                lineHeight: "1.6",
                background: "var(--card)",
                color: "var(--foreground)",
                border: "1px solid var(--border)",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {streamingContent}
              <span
                style={{
                  display: "inline-block",
                  width: "2px",
                  height: "1em",
                  background: "var(--primary)",
                  marginLeft: "2px",
                  animation: "blink 1s step-start infinite",
                  verticalAlign: "text-bottom",
                }}
              />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        style={{
          borderTop: "1px solid var(--border)",
          paddingTop: "1rem",
          display: "flex",
          gap: "0.75rem",
          alignItems: "flex-end",
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={streaming}
          placeholder="Digite sua mensagem… (Enter para enviar, Shift+Enter para nova linha)"
          rows={1}
          style={{
            flex: 1,
            resize: "none",
            padding: "0.625rem 0.875rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--border)",
            background: "var(--background)",
            color: "var(--foreground)",
            fontSize: "0.9375rem",
            lineHeight: "1.5",
            outline: "none",
            fontFamily: "inherit",
            maxHeight: "160px",
            overflowY: "auto",
          }}
          onInput={(e) => {
            const el = e.currentTarget;
            el.style.height = "auto";
            el.style.height = Math.min(el.scrollHeight, 160) + "px";
          }}
        />
        <button
          onClick={sendMessage}
          disabled={streaming || !input.trim()}
          style={{
            padding: "0.625rem 1.25rem",
            borderRadius: "0.5rem",
            background: "var(--primary)",
            color: "var(--primary-foreground)",
            border: "none",
            fontWeight: 600,
            fontSize: "0.9375rem",
            cursor: "pointer",
            opacity: streaming || !input.trim() ? 0.5 : 1,
            whiteSpace: "nowrap",
          }}
        >
          {streaming ? "…" : "Enviar"}
        </button>
      </div>
    </div>
  );
}
