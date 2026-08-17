import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import NavBar from "@/components/NavBar";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin", "cyrillic"],
  variable: "--font-space-grotesk",
  display: "swap",
});
const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Sign Language Translator",
  description: "Перевод жестового языка в текст и речь в реальном времени",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body
        className={`${spaceGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable} font-body bg-graphite-950 text-white antialiased min-h-screen`}
      >
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 w-[32rem] h-[32rem] rounded-full bg-signal-teal/[0.07] blur-3xl" />
          <div className="absolute top-1/3 -right-40 w-[28rem] h-[28rem] rounded-full bg-signal-amber/[0.05] blur-3xl" />
        </div>
        <div className="relative">
          <NavBar />
          {children}
        </div>
      </body>
    </html>
  );
}
