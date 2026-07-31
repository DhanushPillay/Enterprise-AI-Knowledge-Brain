import type { Metadata } from "next";
import { Lora, Inter, Geist_Mono } from "next/font/google";
import "../globals.css";
import { CustomCursor } from "@/components/ui/custom-cursor";
import { PublicSidebar } from "@/components/layout/public-sidebar";

const lora = Lora({ variable: "--font-heading", subsets: ["latin"] });
const inter = Inter({ variable: "--font-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cortexa Chat",
  description: "Enterprise Assistant",
};

export default function PublicLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${lora.variable} ${inter.variable} ${geistMono.variable} font-sans h-full antialiased cursor-none`}
    >
      <body className="h-screen w-screen overflow-hidden bg-[#EAE8E3] text-[#1a1a1a] cursor-none flex flex-row">
        <CustomCursor />
        <PublicSidebar />
        <main className="flex-1 relative overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
