"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, Network, UploadCloud, LayoutDashboard, BrainCircuit } from "lucide-react";

const NAV_ITEMS = [
  { name: "System Overview", href: "/system", icon: MessageSquare },
  { name: "Knowledge Graph", href: "/graph", icon: Network },
  { name: "Ingestion Pipeline", href: "/ingestion", icon: UploadCloud },
  { name: "System Dashboard", href: "/dashboard", icon: LayoutDashboard },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <div className="w-full px-4 pt-8 pb-4">
      <div className="flex items-center gap-3 mb-10 px-2">
        <BrainCircuit className="w-6 h-6 text-accent-dopamine" />
        <div className="font-heading font-bold text-lg tracking-wide text-white">CORTEXA</div>
      </div>
      
      <div className="font-mono text-[9px] uppercase tracking-widest text-white/30 mb-4 px-2">
        System Modules
      </div>
      
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-none border-l-2 transition-all ${
                isActive 
                  ? "border-accent-dopamine bg-white/5 text-white" 
                  : "border-transparent text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              <item.icon className={`w-4 h-4 ${isActive ? "text-accent-dopamine" : ""}`} />
              <span className="font-sans text-[13px] font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
