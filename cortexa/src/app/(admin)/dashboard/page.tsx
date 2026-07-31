import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const BentoCard = ({ title, value, status, className }: { title: string, value: string, status: string, className?: string }) => (
  <div className={cn("group relative flex flex-col justify-between overflow-hidden rounded-2xl bg-white/5 border border-white/10 p-6 transition-all hover:bg-white/10 hover:shadow-2xl hover:border-white/20", className)}>
    <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
    <div className="relative z-10">
      <div className="font-mono text-[9px] uppercase tracking-widest text-foreground/40 mb-4">{title}</div>
      <div className="font-sans text-5xl font-medium text-foreground group-hover:scale-105 transition-transform origin-left">{value}</div>
    </div>
    <div className="relative z-10 font-mono text-[10px] uppercase tracking-widest text-accent-dopamine mt-8 flex items-center gap-2">
      <div className="w-1.5 h-1.5 rounded-full bg-accent-dopamine animate-pulse" />
      {status}
    </div>
  </div>
);

export default function DashboardPage() {
  return (
    <div className="flex-1 w-full h-full p-24 overflow-y-auto">
      <h2 className="font-mono text-accent-dopamine text-[11px] tracking-[0.3em] uppercase mb-6">
        Telemetry // Analytics
      </h2>
      
      <h1 className="font-heading text-foreground text-6xl tracking-tight mb-16">
        System Dashboard.
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 md:grid-rows-2 gap-6 auto-rows-[250px]">
        <BentoCard 
          title="Total Nodes" 
          value="4,821" 
          status="Live Sync" 
          className="md:col-span-2 md:row-span-1"
        />
        <BentoCard 
          title="Active Connections" 
          value="12,044" 
          status="Live Sync" 
          className="md:col-span-1 md:row-span-1"
        />
        <BentoCard 
          title="Query Latency (Avg)" 
          value="142ms" 
          status="Optimal" 
          className="md:col-span-1 md:row-span-1"
        />
        <BentoCard 
          title="Knowledge Graph Density" 
          value="84%" 
          status="Indexing..." 
          className="md:col-span-2 md:row-span-1 bg-gradient-to-br from-white/5 via-black/20 to-accent-dopamine/10"
        />
      </div>
    </div>
  );
}
