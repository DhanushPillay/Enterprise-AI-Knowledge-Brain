"use client";
import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export const BackgroundBeams = ({ className }: { className?: string }) => {
  return (
    <div
      className={cn(
        "absolute inset-0 z-0 overflow-hidden pointer-events-none flex items-center justify-center bg-transparent",
        className
      )}
    >
      <div className="absolute inset-0 bg-transparent [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />
      <svg
        className="absolute inset-0 h-full w-full stroke-white/5"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id="beams-pattern"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
            patternTransform="translate(-1 -1)"
          >
            <path d="M.5 40V.5H40" fill="none" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" strokeWidth="0" fill="url(#beams-pattern)" />
      </svg>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2 }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <div className="w-[800px] h-[800px] bg-accent-dopamine/10 rounded-full blur-[100px] animate-pulse" />
      </motion.div>
    </div>
  );
};
