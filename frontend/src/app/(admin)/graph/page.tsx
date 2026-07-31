"use client";

import { useState, useEffect } from "react";
import { Search, Database, Share2, Layers, AlertCircle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { fetchGraphStats, type GraphStats } from "@/services/api";

export default function GraphPage() {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await fetchGraphStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load graph stats");
      } finally {
        setIsLoading(false);
      }
    }
    
    loadStats();
  }, []);

  return (
    <div className="flex-1 w-full h-full p-12 md:p-24 flex flex-col">
      <div className="flex justify-between items-start mb-16">
        <div>
          <h2 className="font-mono text-accent-dopamine text-[11px] tracking-[0.3em] uppercase mb-6">
            Topology // Semantic Graph
          </h2>
          <h1 className="font-heading text-foreground text-5xl md:text-6xl tracking-tight">
            Knowledge Canvas.
          </h1>
        </div>
        
        <div className="bg-white/50 backdrop-blur-md border border-black/5 rounded-2xl p-4 flex gap-8">
          <div>
            <div className="font-mono text-[9px] uppercase tracking-widest text-[#666] mb-1">Total Nodes</div>
            <div className="font-heading text-3xl text-black">
              {stats ? stats.nodes.reduce((acc, n) => acc + n.count, 0) : "-"}
            </div>
          </div>
          <div>
            <div className="font-mono text-[9px] uppercase tracking-widest text-[#666] mb-1">Total Edges</div>
            <div className="font-heading text-3xl text-black">
              {stats ? stats.relationships.reduce((acc, r) => acc + r.count, 0) : "-"}
            </div>
          </div>
        </div>
      </div>

      <div className="w-full flex-1 flex flex-col lg:flex-row gap-8">
        
        {/* Left Column - Stats */}
        <div className="w-full lg:w-1/3 flex flex-col gap-6">
          {isLoading && (
            <div className="flex-1 bg-white border border-black/5 rounded-3xl p-8 flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 text-black/20 animate-spin mb-4" />
              <div className="font-mono text-sm text-[#666]">Querying Neo4j...</div>
            </div>
          )}

          {error && (
             <div className="bg-red-50 border border-red-200 text-red-600 rounded-3xl p-8 flex flex-col items-center justify-center text-center">
               <AlertCircle className="w-8 h-8 mb-4" />
               <div className="font-sans font-medium mb-2">Connection Failed</div>
               <div className="font-mono text-xs">{error}</div>
             </div>
          )}

          {stats && !isLoading && !error && (
            <>
              {/* Nodes Distribution */}
              <div className="bg-white border border-black/5 rounded-3xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <Database className="w-4 h-4 text-accent-dopamine" />
                  <h3 className="font-sans font-medium text-lg">Entity Types</h3>
                </div>
                <div className="space-y-3">
                  {stats.nodes.map((node, i) => (
                    <div key={i} className="flex justify-between items-center group">
                      <span className="font-mono text-xs text-[#555] group-hover:text-black transition-colors">{node.label}</span>
                      <span className="font-sans font-medium text-sm bg-black/5 px-3 py-1 rounded-full">{node.count}</span>
                    </div>
                  ))}
                  {stats.nodes.length === 0 && (
                    <div className="font-mono text-xs text-[#888] text-center py-4">No entities found in graph.</div>
                  )}
                </div>
              </div>

              {/* Relationships Distribution */}
              <div className="bg-white border border-black/5 rounded-3xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <Share2 className="w-4 h-4 text-accent-dopamine" />
                  <h3 className="font-sans font-medium text-lg">Relationships</h3>
                </div>
                <div className="space-y-3">
                  {stats.relationships.map((rel, i) => (
                    <div key={i} className="flex justify-between items-center group">
                      <span className="font-mono text-xs text-[#555] group-hover:text-black transition-colors">{rel.rel_type}</span>
                      <span className="font-sans font-medium text-sm bg-black/5 px-3 py-1 rounded-full">{rel.count}</span>
                    </div>
                  ))}
                  {stats.relationships.length === 0 && (
                    <div className="font-mono text-xs text-[#888] text-center py-4">No relationships found.</div>
                  )}
                </div>
              </div>

              {/* Vector Store Stats */}
              <div className="bg-white border border-black/5 rounded-3xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <Layers className="w-4 h-4 text-accent-dopamine" />
                  <h3 className="font-sans font-medium text-lg">Vector Store (Chroma)</h3>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs text-[#555]">Embedded Chunks</span>
                  <span className="font-sans font-medium text-sm bg-black/5 px-3 py-1 rounded-full">{stats.total_chunks}</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right Column - Visualization Placeholder */}
        <div className="w-full lg:w-2/3 bg-black/[0.02] border border-black/5 rounded-3xl flex flex-col items-center justify-center p-12 overflow-hidden relative group">
          <div className="absolute -inset-20 bg-gradient-to-tr from-accent-dopamine/10 to-transparent blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
          
          <motion.div 
            animate={{ opacity: [0.3, 0.8, 0.3] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="font-mono text-[9px] uppercase tracking-widest text-[#666] text-center relative z-10"
          >
            <div className="mb-4">
              <Share2 className="w-12 h-12 text-[#ccc] mx-auto opacity-50" />
            </div>
            <div className="mb-2 relative">
              <span className="relative font-bold text-[#333]">[ INTERACTIVE CANVAS ]</span>
            </div>
            <span className="opacity-50">3D Visualization Module coming in v3.0</span>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
