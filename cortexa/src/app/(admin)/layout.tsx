import type { Metadata } from "next";
import { Lora, Inter, Geist_Mono } from "next/font/google";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { ChatStrip } from "@/features/chat/chat-strip";
import "../globals.css";

const lora = Lora({ variable: "--font-heading", subsets: ["latin"] });
const inter = Inter({ variable: "--font-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cortexa Brain",
  description: "Enterprise AI Knowledge Graph",
};

const NoiseFilter = () => (
  <svg className="pointer-events-none absolute inset-0 z-0 h-full w-full opacity-[0.15] mix-blend-overlay" xmlns="http://www.w3.org/2000/svg">
    <filter id="noiseFilter">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch" />
    </filter>
    <rect width="100%" height="100%" filter="url(#noiseFilter)" />
  </svg>
);

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${lora.variable} ${inter.variable} ${geistMono.variable} font-sans h-full antialiased`}
    >
      <body className="flex h-screen w-screen overflow-hidden bg-canvas-bg text-foreground">
        
        {/* Left Command Strip (Dark, Textured, Fixed Width) */}
        <aside className="relative flex w-[400px] shrink-0 flex-col bg-strip-bg text-[#FAFAFA] border-r border-black/20 shadow-2xl z-20">
          <NoiseFilter />
          <div className="relative z-10 flex flex-col h-full">
            <AppSidebar />
            <div className="flex-1 overflow-hidden flex flex-col border-t border-white/10 mt-4 pt-4">
              <ChatStrip />
            </div>
          </div>
        </aside>

        {/* Right Knowledge Canvas (Warm Off-White, Massive Typography) */}
        <main className="flex-1 w-full flex flex-col h-screen overflow-y-auto bg-canvas-bg relative z-10">
          {children}
        </main>

      </body>
    </html>
  );
}
