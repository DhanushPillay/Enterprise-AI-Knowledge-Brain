import { BackgroundBeams } from "@/components/ui/background-beams";
import { TextGenerateEffect } from "@/components/ui/text-generate-effect";

export default function CanvasLandingPage() {
  return (
    <div className="flex-1 w-full h-full p-24 flex flex-col justify-center relative overflow-hidden">
      <BackgroundBeams />
      
      <div className="max-w-4xl relative z-10">
        <h2 className="font-mono text-accent-dopamine text-[11px] tracking-[0.3em] uppercase mb-6">
          System Initialized // Node: Alpha
        </h2>
        
        <h1 className="font-heading text-foreground text-7xl md:text-8xl leading-[0.9] tracking-tight mb-8">
          Enterprise<br/>
          <TextGenerateEffect words="Intelligence" className="text-foreground/40 italic inline-block mt-0 mb-0 font-normal" /><br/>
          Engine.
        </h1>
        
        <div className="w-24 h-1 bg-foreground mb-12" />
        
        <p className="font-sans text-foreground/70 text-xl max-w-2xl leading-relaxed">
          Cortexa is a multi-agent reasoning graph. It ingests your unstructured organizational data, constructs a semantic topology, and traverses it to answer complex queries.
        </p>
        
        <div className="mt-16 flex gap-12">
          <div>
            <div className="font-mono text-[9px] uppercase tracking-widest text-foreground/40 mb-2">Active Agents</div>
            <div className="font-sans font-medium text-2xl text-foreground">3 / 5</div>
          </div>
          <div>
            <div className="font-mono text-[9px] uppercase tracking-widest text-foreground/40 mb-2">Graph Status</div>
            <div className="font-sans font-medium text-2xl text-foreground flex items-center gap-2">
              <div className="w-2 h-2 rounded-full shadow-[0_0_10px_2px_rgba(255,255,255,0.3)] bg-accent-dopamine animate-pulse" />
              Syncing
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
