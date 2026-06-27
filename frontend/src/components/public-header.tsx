"use client";

import { FileCheck2 } from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-bold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <FileCheck2 className="h-5 w-5" />
          </span>
          <span className="text-lg">Papery</span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex dark:text-slate-300">
          <a href="#features" className="hover:text-brand-600">Features</a>
          <a href="#how" className="hover:text-brand-600">How It Works</a>
          <a href="#pricing" className="hover:text-brand-600">Pricing</a>
          <a href="#faq" className="hover:text-brand-600">FAQ</a>
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link href="/login" className="btn-secondary hidden sm:inline-flex">
            Log in
          </Link>
          <Link href="/register" className="btn-primary">
            Sign up
          </Link>
        </div>
      </div>
    </header>
  );
}
