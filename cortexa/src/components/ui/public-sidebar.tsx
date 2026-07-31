"use client";

import { MessageSquare, Settings, Plus, LayoutDashboard } from "lucide-react";
import { MagneticButton } from "./magnetic-button";
import Link from "next/link";

export const PublicSidebar = () => {
  const dummyHistory = [
    { id: 1, title: "Q3 Financial Analysis" },
    { id: 2, title: "Onboarding Docs Query" },
    { id: 3, title: "Graph Database Setup" },
  ];

  return (
    <aside className="w-[260px] h-screen bg-[#F9F9F8] border-r border-black/5 flex flex-col hidden md:flex shrink-0">
      
      {/* Top Action */}
      <div className="p-4">
        <MagneticButton className="w-full flex items-center justify-center gap-2 !py-3">
          <Plus className="w-4 h-4" />
          New Chat
        </MagneticButton>
      </div>

      {/* History */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        <div>
          <div className="px-2 text-xs font-mono tracking-widest text-[#999] uppercase mb-2">Previous 7 Days</div>
          <div className="space-y-1">
            {dummyHistory.map((item) => (
              <button key={item.id} className="hoverable w-full text-left px-2 py-2 text-sm text-[#444] rounded-lg hover:bg-black/5 transition-colors truncate">
                {item.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-3 border-t border-black/5">
        <Link href="/system" className="hoverable flex items-center gap-3 px-3 py-3 text-sm text-[#444] rounded-lg hover:bg-black/5 transition-colors">
          <LayoutDashboard className="w-4 h-4" />
          Admin Dashboard
        </Link>
        <button className="hoverable w-full flex items-center gap-3 px-3 py-3 text-sm text-[#444] rounded-lg hover:bg-black/5 transition-colors">
          <Settings className="w-4 h-4" />
          Settings
        </button>
      </div>

    </aside>
  );
};
