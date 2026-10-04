"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Portfolio Health" },
  { href: "/quote", label: "Quote Calculator" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className="bg-ink text-paper">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 sm:py-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="eyebrow text-route-soft">Illustrative 4PL Portfolio Project</div>
          <h1 className="text-lg sm:text-xl font-display font-bold tracking-tight mt-0.5">
            Freight Pricing &amp; Margin Monitor
          </h1>
        </div>
        <nav className="flex items-center gap-1 -mx-1 sm:mx-0">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`flex-1 sm:flex-none text-center px-4 py-2.5 sm:py-2 text-sm font-medium rounded-sm transition-colors ${
                  active ? "bg-paper text-ink" : "text-paper/70 hover:text-paper hover:bg-ink-700"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="h-px bg-dotted-line opacity-40" />
    </header>
  );
}
