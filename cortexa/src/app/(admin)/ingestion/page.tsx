"use client";

import { motion } from "framer-motion";
import { UploadCloud } from "lucide-react";

export default function IngestionPage() {
  return (
    <div className="flex-1 w-full h-full p-24">
      <h2 className="font-mono text-accent-dopamine text-[11px] tracking-[0.3em] uppercase mb-6">
        Data Operations // Pipeline
      </h2>
      
      <h1 className="font-heading text-foreground text-6xl tracking-tight mb-16">
        Ingestion Engine.
      </h1>

      <motion.div 
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="relative w-full max-w-2xl border-2 border-dashed border-foreground/20 p-16 flex flex-col items-center justify-center cursor-pointer hover:border-accent-dopamine/50 hover:bg-white/5 transition-colors group rounded-3xl overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-accent-dopamine/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <motion.div 
          animate={{ y: [0, -8, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="mb-8"
        >
          <UploadCloud className="w-16 h-16 text-foreground/30 group-hover:text-accent-dopamine transition-colors drop-shadow-xl" />
        </motion.div>
        
        <div className="relative z-10 font-mono text-[9px] uppercase tracking-widest text-foreground/40 mb-6 group-hover:text-accent-dopamine transition-colors">Supported Formats: PDF, DOCX, TXT</div>
        <div className="relative z-10 font-sans text-2xl font-medium text-foreground text-center">
          Drop organizational data here<br/>
          <span className="text-foreground/50 text-lg">to begin graph extraction.</span>
        </div>
      </motion.div>
    </div>
  );
}
