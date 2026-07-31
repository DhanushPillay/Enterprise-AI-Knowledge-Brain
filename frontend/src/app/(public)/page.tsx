"use client";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { ArrowUp, Brain, Loader2, ChevronDown, Shield, Database } from "lucide-react";
import { useChatStore, type Message } from "@/store/chat-store";

export default function PublicChatbot() {
  const { messages, isLoading, sendMessage } = useChatStore();
  const [input, setInput] = useState("");
  const [expandedSources, setExpandedSources] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input;
    setInput("");
    await sendMessage(query);
  };

  return (
    <div className="flex flex-col h-full w-full relative">
      
      {/* Dynamic Header - Disappears on Chat */}
      <AnimatePresence>
        {messages.length === 0 && (
          <motion.header 
            initial={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20, height: 0 }}
            className="flex justify-between items-start pt-12 px-12 mb-8 w-full max-w-[1400px] mx-auto overflow-hidden shrink-0"
          >
            <div>
              <h1 className="font-heading text-6xl md:text-8xl tracking-tighter leading-[0.85] text-[#111]">
                Ask<br/>
                Cortexa.
              </h1>
            </div>
            <div className="text-right mt-4 hidden md:block">
              <div className="font-mono text-[9px] uppercase tracking-[0.3em] text-[#666] leading-relaxed">
                Enterprise Knowledge<br/>Retrieval System<br/>v2.0
              </div>
            </div>
          </motion.header>
        )}
      </AnimatePresence>

      {/* Main Chat Container */}
      <div className="flex flex-col flex-1 w-full max-w-3xl mx-auto relative h-full min-h-0 px-4">
        
        {/* Chat Area */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto pt-8 pb-32 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
        >
          <AnimatePresence>
            {messages.length === 0 && (
              <motion.div 
                key="empty-state"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col justify-center items-center text-center text-[#888] pt-12"
              >
                <p className="font-sans text-xl max-w-md mx-auto leading-relaxed mb-8">
                  Ask a question to explore the organizational knowledge graph.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mx-auto">
                  {[
                    "Analyze our Q3 financial reports",
                    "What are the latest compliance guidelines?",
                    "Summarize the recent engineering all-hands",
                    "Explain our standard deployment architecture"
                  ].map((suggestion, i) => (
                    <button 
                      key={`suggestion-${i}`}
                      onClick={() => setInput(suggestion)}
                      className="hoverable text-left px-6 py-4 bg-white/50 rounded-2xl border border-black/5 hover:bg-white hover:border-black/10 transition-all text-sm text-[#555] font-sans"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            <div className="space-y-8 flex flex-col">
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`max-w-[85%] ${msg.role === 'user' ? 'self-end' : 'self-start'}`}
                >
                  {/* Sender label */}
                  <div className={`font-mono text-[9px] uppercase tracking-widest mb-2 flex items-center gap-2 ${msg.role === 'user' ? 'justify-end text-[#999]' : 'text-[#333]'}`}>
                    {msg.role === 'assistant' && <Brain className="w-3 h-3" />}
                    {msg.role === 'user' ? 'You' : 'Cortexa'}
                    {msg.is_safe === false && (
                      <span className="text-red-500 flex items-center gap-1">
                        <Shield className="w-3 h-3" /> BLOCKED
                      </span>
                    )}
                  </div>

                  {/* Message body */}
                  <div className={`text-lg leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'text-[#111] text-right' : 'text-[#444]'}`}>
                    {msg.content}
                  </div>

                  {/* Reasoning & Sources (assistant messages only) */}
                  {msg.role === 'assistant' && (msg.reasoning?.length || msg.sources?.length) && (
                    <div className="mt-3">
                      <button
                        onClick={() => setExpandedSources(expandedSources === msg.id ? null : msg.id)}
                        className="flex items-center gap-2 text-xs font-mono text-[#999] hover:text-[#555] transition-colors"
                      >
                        <Database className="w-3 h-3" />
                        {msg.sources?.length || 0} sources · {msg.reasoning?.length || 0} steps
                        <ChevronDown className={`w-3 h-3 transition-transform ${expandedSources === msg.id ? 'rotate-180' : ''}`} />
                      </button>

                      <AnimatePresence>
                        {expandedSources === msg.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            {/* Reasoning trace */}
                            {msg.reasoning && msg.reasoning.length > 0 && (
                              <div className="mt-2 p-3 bg-black/[0.02] rounded-xl border border-black/5">
                                <div className="font-mono text-[9px] uppercase tracking-widest text-[#999] mb-2">Reasoning</div>
                                <ol className="space-y-1">
                                  {msg.reasoning.map((step, i) => (
                                    <li key={`reason-${msg.id}-${i}`} className="text-xs text-[#666] font-mono flex gap-2">
                                      <span className="text-[#aaa] shrink-0">{i + 1}.</span>
                                      {step}
                                    </li>
                                  ))}
                                </ol>
                              </div>
                            )}

                            {/* Sources */}
                            {msg.sources && msg.sources.length > 0 && (
                              <div className="mt-2 space-y-2">
                                {msg.sources.map((source, i) => (
                                  <div
                                    key={`source-${msg.id}-${i}`}
                                    className="p-3 bg-black/[0.02] rounded-xl border border-black/5"
                                  >
                                    <div className="flex justify-between items-center mb-1">
                                      <span className="text-xs font-mono font-medium text-[#555]">
                                        {source.name}
                                      </span>
                                      <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full ${
                                        source.type === 'graph'
                                          ? 'bg-emerald-100 text-emerald-700'
                                          : 'bg-blue-100 text-blue-700'
                                      }`}>
                                        {source.type}
                                      </span>
                                    </div>
                                    <p className="text-xs text-[#888] line-clamp-2">
                                      {source.snippet}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </motion.div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="self-start max-w-[80%]"
                >
                  <div className="font-mono text-[9px] uppercase tracking-widest mb-2 text-[#333] flex items-center gap-2">
                    <Brain className="w-3 h-3" /> Cortexa
                  </div>
                  <div className="flex items-center gap-3 text-[#888]">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm font-mono">Searching knowledge graph...</span>
                  </div>
                </motion.div>
              )}
            </div>
          </AnimatePresence>
        </div>

        {/* Input Area (Anchored to bottom) */}
        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#EAE8E3] via-[#EAE8E3] to-transparent pointer-events-none">
          <div className="relative group hoverable max-w-3xl mx-auto pointer-events-auto shadow-xl shadow-black/5 rounded-3xl">
            <form onSubmit={handleSubmit} className="flex flex-col bg-white rounded-3xl p-3 border border-black/5 transition-shadow hover:shadow-md">
              
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="What do you want to know?"
                className="w-full bg-transparent border-none outline-none font-sans text-lg py-2 px-3 placeholder:text-[#aaa] focus:ring-0"
                disabled={isLoading}
              />
              
              <div className="flex justify-between items-center mt-2">
                <div className="flex items-center gap-1">
                  <button type="button" className="p-2 text-[#666] hover:text-black hover:bg-black/5 rounded-full transition-colors" title="Attach File">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                  </button>
                  <button type="button" className="p-2 text-[#666] hover:text-black hover:bg-black/5 rounded-full transition-colors" title="Search Web">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                  </button>
                </div>
                
                <MagneticButton
                  type="submit"
                  className={`!p-2.5 flex-shrink-0 ${isLoading ? '!bg-gray-400' : '!bg-black hover:!bg-black/80'} text-white`}
                >
                  {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowUp className="w-5 h-5" />}
                </MagneticButton>
              </div>

            </form>
          </div>
        </div>

      </div>
    </div>
  );
}
