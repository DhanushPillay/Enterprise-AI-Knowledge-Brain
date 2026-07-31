"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { Upload, ArrowUp } from "lucide-react";

export default function PublicChatbot() {
  const [messages, setMessages] = useState<{id: string, text: string, sender: 'user'|'ai'}[]>([]);
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, { id: Date.now().toString(), text: input, sender: 'user' }]);
    setInput("");
    
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: (Date.now() + 1).toString(), 
        text: "I am analyzing your organizational data. This is a bespoke, human-crafted interface.", 
        sender: 'ai' 
      }]);
    }, 1500);
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

      {/* Main Chat Container - Centered */}
      <div className="flex flex-col flex-1 w-full max-w-3xl mx-auto relative h-full min-h-0 px-4">
        
        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto pt-8 pb-32 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
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
                      key={i}
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
                  className={`max-w-[80%] ${msg.sender === 'user' ? 'self-end' : 'self-start'}`}
                >
                  <div className={`font-mono text-[9px] uppercase tracking-widest mb-2 ${msg.sender === 'user' ? 'text-right text-[#999]' : 'text-left text-[#333]'}`}>
                    {msg.sender === 'user' ? 'You' : 'Cortexa'}
                  </div>
                  <div className={`text-xl leading-relaxed ${msg.sender === 'user' ? 'text-[#111] text-right' : 'text-[#444] font-heading text-2xl'}`}>
                    {msg.text}
                  </div>
                </motion.div>
              ))}
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
              />
              
              <div className="flex justify-between items-center mt-2">
                <div className="flex items-center gap-1">
                  <button type="button" className="p-2 text-[#666] hover:text-black hover:bg-black/5 rounded-full transition-colors" title="Attach File">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                  </button>
                  <button type="button" className="p-2 text-[#666] hover:text-black hover:bg-black/5 rounded-full transition-colors" title="Search Web">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                  </button>
                  <button type="button" className="p-2 text-[#666] hover:text-black hover:bg-black/5 rounded-full transition-colors" title="Voice Input">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
                  </button>
                </div>
                
                <MagneticButton type="submit" className="!p-2.5 !bg-black text-white hover:!bg-black/80 flex-shrink-0">
                  <ArrowUp className="w-5 h-5" />
                </MagneticButton>
              </div>

            </form>
          </div>
        </div>

      </div>
    </div>
  );
}
