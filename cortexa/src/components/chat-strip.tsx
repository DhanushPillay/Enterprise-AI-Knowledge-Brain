"use client";

import { useState } from "react";
import { Send, Target, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  isLoading?: boolean;
};

export function ChatStrip() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;
    
    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    const tempId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: tempId, role: "assistant", content: "", isLoading: true }]);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content })
      });

      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();

      setMessages(prev => prev.map(msg => msg.id === tempId ? {
        id: tempId,
        role: "assistant",
        content: data.answer,
      } : msg));
    } catch (error) {
      console.error(error);
      setMessages(prev => prev.map(msg => msg.id === tempId ? {
        id: tempId,
        role: "assistant",
        content: "[ERR] CONNECTION TO GRAPH BACKEND FAILED."
      } : msg));
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-transparent px-4 pb-6">
      
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 px-2">
        <Target className="w-4 h-4 text-accent-dopamine" />
        <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-white/50">Terminal / Chat</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 px-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {messages.length === 0 && (
          <div className="font-mono text-[11px] text-white/30 uppercase tracking-widest mt-8 flex flex-col gap-2">
            <div>&gt; SYSTEM INITIALIZED</div>
            <div>&gt; AWAITING QUERY INPUT...</div>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div 
              key={msg.id} 
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="flex flex-col gap-1 w-full"
            >
              <div className="font-mono text-[9px] tracking-widest uppercase text-white/30 mb-1 flex items-center gap-1">
                <ChevronRight className="w-3 h-3 text-accent-dopamine" />
                {msg.role === "user" ? "USER_INPUT" : "CORTEXA_RESPONSE"}
              </div>
              
              <div className={`text-[13px] leading-relaxed font-sans ${msg.role === "user" ? "text-white/90" : "text-white/70"}`}>
                {msg.isLoading ? (
                  <div className="flex items-center gap-2 text-accent-dopamine font-mono text-[10px] uppercase tracking-widest">
                    <div className="flex gap-[2px]">
                      <motion.div className="w-1 h-3 bg-accent-dopamine" animate={{ scaleY: [1, 2, 1] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0 }} />
                      <motion.div className="w-1 h-3 bg-accent-dopamine" animate={{ scaleY: [1, 2, 1] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.2 }} />
                      <motion.div className="w-1 h-3 bg-accent-dopamine" animate={{ scaleY: [1, 2, 1] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.4 }} />
                    </div> Processing Graph...
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Input */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <form onSubmit={handleSubmit} className="relative flex items-center group">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Initialize query..."
            disabled={isTyping}
            className="w-full bg-black/20 border border-white/10 rounded-none px-4 py-3 text-[13px] text-white placeholder:text-white/30 placeholder:font-mono placeholder:text-[11px] placeholder:tracking-widest focus:outline-none focus:border-accent-dopamine/50 transition-colors"
          />
          <button 
            type="submit"
            className="absolute right-2 p-1.5 bg-accent-dopamine text-black hover:bg-accent-dopamine/80 transition-colors disabled:opacity-30"
            disabled={!input.trim() || isTyping}
          >
            <Send className="w-3 h-3 ml-[1px]" />
          </button>
        </form>
      </div>
    </div>
  );
}
