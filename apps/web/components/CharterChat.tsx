"use client";

import { useState, useEffect, useRef } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function CharterChat({ uploadId }: { uploadId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await fetch(`/api/agents/${uploadId}/charter/messages`);
        if (res.ok) {
          const data = await res.json();
          setMessages(data);
        }
      } catch (e) {
        console.error("Failed to fetch messages", e);
      }
    };

    if (uploadId) {
      fetchMessages();
    }
  }, [uploadId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await fetch(`/api/agents/${uploadId}/charter/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.content }),
      });
      if (res.ok) {
        const aiMsg = await res.json();
        setMessages(prev => [...prev, aiMsg]);
      }
    } catch (e) {
      console.error("Failed to send message", e);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-zinc-50/50 relative">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-zinc-400 text-sm text-center mt-20 flex flex-col items-center">
            <div className="w-16 h-16 bg-zinc-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            No messages yet. Ask the Charter Agent about the evaluation.
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`rounded-2xl px-5 py-3.5 max-w-[85%] whitespace-pre-wrap shadow-sm ${
                m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-white border border-zinc-200 text-zinc-800 rounded-tl-sm'
              }`}>
                {m.content}
              </div>
            </div>
          ))
        )}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-white border border-zinc-200 text-zinc-400 rounded-2xl rounded-tl-sm px-5 py-3 shadow-sm flex items-center gap-1">
              <div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-4 border-t border-zinc-200 bg-white">
        <div className="flex gap-3 max-w-4xl mx-auto relative">
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about the evaluation or requirements..."
            className="flex-1 bg-zinc-100 border-transparent rounded-xl px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:bg-white transition-all text-zinc-900"
            disabled={sending}
          />
          <button 
            onClick={sendMessage}
            disabled={!input.trim() || sending}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3.5 rounded-xl disabled:opacity-50 font-medium transition-colors shadow-sm"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
