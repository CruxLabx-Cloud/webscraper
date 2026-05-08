"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, Radar } from "lucide-react";
import { Button } from "@/components/ui/button";

const NAV_LINKS = [
  { href: "/", label: "Companies" },
  { href: "/leads", label: "Find Clients" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/settings", label: "Settings" },
];

export function SiteNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-sky-100/70 bg-white/75 backdrop-blur-xl">
      <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-5 md:px-8">
        <Link href="/" className="group flex items-center gap-3 font-semibold">
          <span className="grid h-9 w-9 place-items-center rounded-xl border border-sky-200 bg-gradient-to-br from-sky-500 to-cyan-400 text-white shadow-sm transition-transform group-hover:scale-105">
            <Building2 className="h-4 w-4" />
          </span>
          <span className="leading-tight">
            <span className="block text-sm text-slate-500">Intelligence OS</span>
            <span className="block text-base text-slate-900">Pipeline Console</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 rounded-xl border border-slate-200/80 bg-white/70 p-1 shadow-sm md:flex">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <Link href="/settings">
            <Button variant="outline" size="sm" className="border-sky-200 bg-white/70">
              <Radar className="h-4 w-4" />
              Settings
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}