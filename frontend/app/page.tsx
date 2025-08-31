"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Plus, SendHorizonal, FileText, X, Image as ImageIcon } from "lucide-react";

type Role = "user" | "assistant";
type Attachment = { name: string; type: string };
type Msg = { id: string; role: Role; content: string; attachments?: Attachment[] };

function Avatar({ role }: { role: Role }) {
  return (
    <div className={clsx(
      "h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold border border-[var(--border)]",
      role === "assistant" ? "bg-[#0f1824]" : "bg-[#172131]"
    )}>
      {role === "assistant" ? "A" : "U"}
    </div>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={clsx("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && <Avatar role="assistant" />}
      <div className={clsx(
        "border border-[var(--border)] rounded-2xl p-4 max-w-[min(820px,92vw)]",
        isUser ? "bg-[var(--bubble-user)]" : "bg-[var(--bubble-assistant)]"
      )}>
        <div className="markdown prose prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {msg.content || ""}
          </ReactMarkdown>
        </div>
        {!!msg.attachments?.length && (
          <div className="mt-3 grid grid-cols-3 gap-2">
            {msg.attachments.map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-[var(--muted)] border border-[var(--border)] rounded-md px-2 py-1">
                {f.type.startsWith("image/") ? <ImageIcon size={16}/> : <FileText size={16}/>}
                <span className="truncate">{f.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      {isUser && <Avatar role="user" />}
    </div>
  );
}

type Preview = { url: string; name: string; isImage: boolean; index: number };

export default function Page() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);

  // autoscroll
  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading, pending.length]);

  // previews
  const previews: Preview[] = useMemo(() => pending.map((f, i) => ({
    url: URL.createObjectURL(f), name: f.name, isImage: f.type.startsWith("image/"), index: i
  })), [pending]);
  useEffect(() => () => previews.forEach(p => URL.revokeObjectURL(p.url)), [previews]);

  // paste
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const files = e.clipboardData?.files;
      if (files?.length) {
        const arr = Array.from(files).filter(f => /image|pdf/i.test(f.type));
        if (arr.length) setPending(p => [...p, ...arr]);
      }
    };
    window.addEventListener("paste", onPaste as any);
    return () => window.removeEventListener("paste", onPaste as any);
  }, []);

  // drag overlay
  const [dragging, setDragging] = useState(false);
  useEffect(() => {
    const onOver = (e: DragEvent) => { e.preventDefault(); setDragging(true); };
    const onDrop = () => setDragging(false);
    const onLeave = () => setDragging(false);
    document.addEventListener("dragover", onOver);
    document.addEventListener("drop", onDrop);
    document.addEventListener("dragleave", onLeave);
    return () => { document.removeEventListener("dragover", onOver); document.removeEventListener("drop", onDrop); document.removeEventListener("dragleave", onLeave); };
  }, []);
  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const arr = Array.from(e.dataTransfer.files).filter(f => /image|pdf/i.test(f.type));
    if (arr.length) setPending(p => [...p, ...arr]);
    setDragging(false);
  };

  const addFiles = (files: File[]) => {
    const arr = files.filter(f => /image|pdf/i.test(f.type));
    if (arr.length) setPending(p => [...p, ...arr]);
  };
  const removePending = (idx: number) => setPending(p => p.filter((_, i) => i !== idx));

  async function send() {
    if (!input.trim() && pending.length === 0) return;

    const filesToSend = pending;
    const userMsg: Msg = {
      id: crypto.randomUUID(), role: "user", content: input,
      attachments: filesToSend.map(f => ({ name: f.name, type: f.type }))
    };
    setMessages(prev => [...prev, userMsg]);

    const aid = crypto.randomUUID();
    setMessages(prev => [...prev, { id: aid, role: "assistant", content: "" }]);

    setInput("");
    setPending([]);
    setLoading(true);

    try {
      const form = new FormData();
      form.append("message", userMsg.content || "");
      form.append("history", JSON.stringify(messages.map(m => ({ role: m.role, content: m.content }))));
      form.append("model_id", "Qwen/Qwen2-VL-2B-Instruct");
      form.append("quant_4bit", "true");
      form.append("use_cpu", "false");
      form.append("max_image_edge", "1024");
      form.append("max_new_tokens", "512");
      filesToSend.forEach(f => form.append("files", f));

      const res = await fetch("http://127.0.0.1:8000/api/v1/chat/stream", { method: "POST", body: form });
      if (!res.ok || !res.body) {
        const msg = await res.text();
        setMessages(prev => prev.map(m => m.id === aid ? ({ ...m, content: `Error: ${msg}` }) : m));
      } else {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // Parse SSE frames without trimming away leading spaces
          const frames = buffer.split("\n\n");
          buffer = frames.pop() || "";
          for (const f of frames) {
            // Expect "data: ..." lines
            const idx = f.indexOf("data:");
            if (idx === -1) continue;
            const payload = f.slice(idx + 5); // keep exact spacing after "data:"
            if (payload.trim() === "[DONE]") continue;
            setMessages(prev =>
              prev.map(m => m.id === aid ? ({ ...m, content: (m.content || "") + payload }) : m)
            );
          }
        }
      }
    } catch (e: any) {
      setMessages(prev => prev.map(m => m.id === aid ? ({ ...m, content: "Error: " + (e?.message || "unknown") }) : m));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen grid grid-rows-[56px_1fr_auto]">
      <header className="border-b border-[var(--border)] px-4 flex items-center justify-between">
        <div className="font-semibold">ValorMM</div>
        <div className="text-sm text-[var(--muted)]">Local • Qwen2-VL-2B</div>
      </header>

      <main ref={scrollerRef} className="overflow-y-auto p-4 scrollbar-thin" onDrop={onDrop} onDragOver={(e)=>e.preventDefault()}>
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map(m => (
            <div key={m.id}><Bubble msg={m} /></div>
          ))}

          {!!previews.length && (
            <div className="max-w-[min(820px,92vw)] mx-auto border border-[var(--border)] rounded-2xl p-4 bg-[var(--panel)]">
              <div className="text-sm text-[var(--muted)] mb-2">Attachments</div>
              <div className="grid grid-cols-3 gap-3">
                {previews.map(p => (
                  <div key={p.index} className="relative border border-[var(--border)] rounded-lg overflow-hidden" title={p.name}>
                    {p.isImage ? (
                      <img src={p.url} alt={p.name} className="h-28 w-full object-cover" />
                    ) : (
                      <div className="h-28 w-full flex flex-col items-center justify-center gap-2 bg-[#0e1620]">
                        <FileText size={20} />
                        <div className="text-xs text-[var(--muted)] px-2 text-center truncate w-full">{p.name}</div>
                      </div>
                    )}
                    <button onClick={() => removePending(p.index)} className="absolute top-1 right-1 bg-black/60 hover:bg-black/80 rounded-md p-1" title="Remove">
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-[var(--border)] p-3 bg-[var(--panel)]">
        <div className="max-w-4xl mx-auto flex gap-2 items-end">
          <button onClick={() => document.getElementById("filepick")?.click()}
                  className="h-11 w-11 rounded-xl bg-[#151c27] border border-[var(--border)] hover:bg-[#192231] flex items-center justify-center"
                  title="Attach files">
            <Plus size={18}/>
          </button>
          <input id="filepick" type="file" multiple accept="image/*,.pdf" className="hidden"
                 onChange={(e) => { const files = Array.from(e.target.files || []); addFiles(files); (e.target as HTMLInputElement).value = ""; }} />

          <textarea
            value={input}
            onChange={(e)=>setInput(e.target.value)}
            placeholder="Message ValorMM… (paste images/PDFs with Ctrl+V)"
            className="flex-1 bg-[#0f1620] border border-[var(--border)] rounded-xl p-3 min-h-[52px] max-h-48 focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            rows={1}
            onKeyDown={(e)=>{ if(e.key === "Enter" && !e.shiftKey){ e.preventDefault(); send(); } }}
          />
          <button onClick={send} disabled={loading}
                  className="h-11 px-4 rounded-xl bg-[#2563eb] hover:bg-[#1d4ed8] disabled:opacity-50 flex items-center gap-2">
            <SendHorizonal size={16}/> Send
          </button>
        </div>
      </footer>
    </div>
  );
}
