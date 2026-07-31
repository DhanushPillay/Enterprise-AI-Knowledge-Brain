"use client";

import { Search } from "lucide-react";
import { motion } from "framer-motion";

export default function GraphPage() {
  return (
    <div className="flex-1 w-full h-full p-24 flex flex-col">
      <h2 className="font-mono text-accent-dopamine text-[11px] tracking-[0.3em] uppercase mb-6">
        Topology // Semantic Graph
      </h2>
      
      <h1 className="font-heading text-foreground text-6xl tracking-tight mb-12">
        Knowledge Canvas.
      </h1>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md relative group mb-16"
      >
        <div className="absolute -inset-1 bg-gradient-to-r from-accent-dopamine/50 to-transparent blur opacity-0 group-hover:opacity-100 transition duration-1000 group-hover:duration-200" />
        <div className="relative border-b-2 border-foreground pb-2 flex items-center gap-4 bg-canvas-bg transition-colors">
          <Search className="w-5 h-5 text-foreground/50 group-hover:text-accent-dopamine transition-colors" />
          <input 
            type="text" 
            placeholder="Search entities and relationships..." 
            className="bg-transparent border-none outline-none flex-1 font-sans text-lg text-foreground placeholder:text-foreground/30 focus:ring-0"
          />
        </div>
      </motion.div>

      <div className="flex-1 w-full flex items-center justify-center">
        <motion.div 
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="font-mono text-[9px] uppercase tracking-widest text-foreground/40 text-center"
        >
          <div className="mb-2 relative">
            <div className="absolute inset-0 bg-accent-dopamine blur-2xl opacity-20" />
            <span className="relative">[ GRAPH VISUALIZATION OFFLINE ]</span>
          </div>
          <span className="opacity-50">WAITING FOR NEO4J SYNC</span>
        </motion.div>
      </div>
    </div>
  );
}
