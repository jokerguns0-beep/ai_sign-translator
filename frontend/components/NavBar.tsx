"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Hand, MessagesSquare } from "lucide-react";

const TABS = [
  { href: "/", label: "Перевод", icon: Hand },
  { href: "/reply", label: "Ответить", icon: MessagesSquare },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-20 backdrop-blur-xl bg-graphite-950/80 border-b border-graphite-800">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-3 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <span className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-signal-teal to-signal-teal/40 shadow-[0_0_20px_-4px_rgba(63,214,194,0.6)]">
            <Hand className="w-4 h-4 text-graphite-950" strokeWidth={2.5} />
          </span>
          <span className="font-display text-sm md:text-base font-medium text-white tracking-tight hidden sm:block">
            Sign<span className="text-signal-teal">Translate</span>
          </span>
        </Link>

        <div className="flex items-center gap-1 bg-graphite-900 border border-graphite-700 rounded-full p-1">
          {TABS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs md:text-sm font-body transition-all ${
                  active
                    ? "bg-signal-teal text-graphite-950 font-medium shadow-[0_0_16px_-4px_rgba(63,214,194,0.7)]"
                    : "text-graphite-600 hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
