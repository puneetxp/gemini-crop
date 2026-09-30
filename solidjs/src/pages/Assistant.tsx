import { Component, createSignal, For } from "solid-js";
import { apiClient } from "../lib/api-client";

export const Assistant: Component = () => {
  const [messages, setMessages] = createSignal([
    {
      sender: "ai",
      text: "Namaste! I am your CropSense AI Farm Assistant. You can speak or type in Hindi, Punjabi, Marathi, or English. How can I help with your crops or livestock today?",
      time: "Just now",
    },
  ]);
  const [inputText, setInputText] = createSignal("");
  const [isSending, setIsSending] = createSignal(false);

  const sendMessage = async (e?: Event) => {
    if (e) e.preventDefault();
    const query = inputText().trim();
    if (!query || isSending()) return;

    const userMsg = { sender: "user", text: query, time: "Now" };
    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setIsSending(true);

    try {
      const res = await apiClient.post("/voice/assist", { text: query, query });
      const reply = res.data?.response || res.data?.data?.reply;
      if (res.ok && reply) {
        setMessages((prev) => [...prev, { sender: "ai", text: reply, time: "Now" }]);
      } else {
        const unavailable = res.ok && res.data?.data?.fallback;
        setMessages((prev) => [
          ...prev,
          {
            sender: "ai",
            text: unavailable
              ? "Sorry, the AI assistant is unavailable right now. Please try again in a moment."
              : `Sorry, I couldn't answer that (error ${res.status}). Please try again.`,
            time: "Now",
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: "Sorry, I couldn't reach the assistant. Check your connection and try again.", time: "Now" },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div class="max-w-4xl mx-auto h-[80vh] flex flex-col bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
      {/* Header */}
      <div class="p-4 border-b border-slate-200/80 bg-slate-50/70 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-forest text-white flex items-center justify-center shadow-sm">
            <span class="material-symbols-outlined text-2xl">smart_toy</span>
          </div>
          <div>
            <h2 class="font-bold text-slate-900 text-sm">CropSense AI Voice & Text Agronomist</h2>
            <div class="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Gemini 2.5 Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <For each={messages()}>
          {(msg) => (
            <div
              class={`flex items-start gap-2.5 max-w-[85%] ${
                msg.sender === "user" ? "ml-auto flex-row-reverse" : ""
              }`}
            >
              <div
                class={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                  msg.sender === "user"
                    ? "bg-forest text-white"
                    : "bg-emerald-100 text-emerald-900"
                }`}
              >
                {msg.sender === "user" ? "You" : "AI"}
              </div>
              <div
                class={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === "user"
                    ? "bg-forest text-white rounded-tr-none shadow-sm"
                    : "bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200/60"
                }`}
              >
                {msg.text}
              </div>
            </div>
          )}
        </For>
        {isSending() && (
          <div class="flex items-center gap-2 text-xs text-slate-400 p-2">
            <span class="w-4 h-4 border-2 border-forest border-t-transparent rounded-full animate-spin"></span>
            <span>Agronomist is analyzing telemetry…</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={sendMessage} class="p-3 border-t border-slate-200 bg-slate-50 flex items-center gap-2">
        <input
          type="text"
          value={inputText()}
          onInput={(e) => setInputText(e.currentTarget.value)}
          placeholder="Ask anything about your crops, soil test, or livestock symptoms…"
          class="flex-1 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-forest text-slate-900"
        />
        <button
          type="submit"
          disabled={!inputText().trim() || isSending()}
          class="p-2.5 bg-forest hover:bg-forest-light text-white rounded-xl shadow disabled:opacity-50 transition-all flex items-center justify-center"
        >
          <span class="material-symbols-outlined text-lg">send</span>
        </button>
      </form>
    </div>
  );
};
