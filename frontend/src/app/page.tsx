import {
  ArrowRight,
  CheckCircle2,
  FileSearch,
  Gauge,
  ScanText,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import Link from "next/link";

import { PublicHeader } from "@/components/public-header";

const features = [
  {
    icon: ScanText,
    title: "Automatic OCR",
    desc: "Reads scanned PDFs, photos, and rotated documents — no manual setup. (Coming next phase.)",
  },
  {
    icon: FileSearch,
    title: "Smart Field Extraction",
    desc: "Pulls Booking No, B/L No, containers, weights, ports and more into structured data.",
  },
  {
    icon: Sparkles,
    title: "AI Comparison",
    desc: "Compares every field across documents and flags mismatches with severity.",
  },
  {
    icon: ShieldCheck,
    title: "Severity & Audit",
    desc: "Critical / Major / Minor classification with a full audit trail.",
  },
  {
    icon: Gauge,
    title: "Fast & Scalable",
    desc: "Asynchronous processing built to handle 300+ page documents.",
  },
  {
    icon: Workflow,
    title: "Reports",
    desc: "Generate PDF, Excel, and JSON verification reports in one click.",
  },
];

const steps = [
  { n: "1", title: "Upload", desc: "Add your reference and target documents." },
  { n: "2", title: "AI verifies", desc: "Papery extracts and compares every field." },
  { n: "3", title: "Get report", desc: "Review mismatches and download the report." },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "/mo",
    docs: "50 documents / month",
    users: "Up to 3 users",
    cta: "Start free",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$99",
    period: "/mo",
    docs: "500 documents / month",
    users: "Up to 10 users",
    cta: "Start Pro",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "$499",
    period: "/mo",
    docs: "5,000 documents / month",
    users: "Up to 100 users",
    cta: "Contact sales",
    highlight: false,
  },
];

const faqs = [
  {
    q: "What file types are supported?",
    a: "PDF, DOCX, PNG, JPG, JPEG and TIFF — including mixed combinations.",
  },
  {
    q: "Do I need to choose an OCR mode?",
    a: "No. Papery automatically detects whether a document needs OCR and handles it.",
  },
  {
    q: "Is my data secure?",
    a: "Yes. Encrypted storage, role-based access control, and a complete audit trail.",
  },
  {
    q: "Which industries are supported?",
    a: "We start with Freight Forwarding & Logistics and expand to all business documents.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <PublicHeader />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 dark:border-brand-800 dark:bg-brand-900/30 dark:text-brand-300">
              <Sparkles className="h-3.5 w-3.5" /> AI Document Verification
            </span>
            <h1 className="mt-6 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
              Stop checking documents by hand.
              <span className="block text-brand-600">Papery verifies them in seconds.</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
              Upload your shipping documents and Papery finds every mismatch —
              wrong container numbers, weights, consignees and more — then proves it
              with a report.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/register" className="btn-primary w-full sm:w-auto">
                Start free <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/login" className="btn-secondary w-full sm:w-auto">
                Log in
              </Link>
            </div>
          </div>

          {/* Visual */}
          <div className="mx-auto mt-16 max-w-4xl">
            <div className="grid grid-cols-1 items-center gap-4 sm:grid-cols-[1fr_auto_1fr]">
              <div className="card">
                <p className="text-xs font-semibold uppercase text-slate-400">Reference</p>
                <p className="mt-2 font-mono text-sm">Booking: SITGUAYE12345</p>
                <p className="font-mono text-sm">Container: TCLU1234567</p>
                <p className="font-mono text-sm">Weight: 26,557.68 kg</p>
              </div>
              <div className="flex justify-center">
                <div className="rounded-full bg-brand-600 p-3 text-white">
                  <ArrowRight className="h-5 w-5" />
                </div>
              </div>
              <div className="card border-rose-200 dark:border-rose-900/50">
                <p className="text-xs font-semibold uppercase text-slate-400">Target</p>
                <p className="mt-2 font-mono text-sm">Booking: SITGUAYE12345</p>
                <p className="font-mono text-sm text-rose-600">
                  Container: TCLU1234561 ✖
                </p>
                <p className="font-mono text-sm text-amber-600">Weight: 26557.680 kg</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-slate-200 bg-slate-50 py-20 dark:border-slate-800 dark:bg-slate-900/40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">Everything you need to verify documents</h2>
            <p className="mt-3 text-slate-600 dark:text-slate-300">
              Built for freight forwarding today, every business document tomorrow.
            </p>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="card">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">How it works</h2>
            <p className="mt-3 text-slate-600 dark:text-slate-300">Three steps, no manual comparison.</p>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
            {steps.map((s) => (
              <div key={s.n} className="card text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">
                  {s.n}
                </div>
                <h3 className="mt-4 font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-slate-200 bg-slate-50 py-20 dark:border-slate-800 dark:bg-slate-900/40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">Simple, transparent pricing</h2>
            <p className="mt-3 text-slate-600 dark:text-slate-300">
              Activate your plan with a company license key.
            </p>
          </div>
          <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
            {plans.map((p) => (
              <div
                key={p.name}
                className={`card flex flex-col ${
                  p.highlight ? "ring-2 ring-brand-600" : ""
                }`}
              >
                {p.highlight && (
                  <span className="mb-3 self-start rounded-full bg-brand-600 px-3 py-1 text-xs font-semibold text-white">
                    Most popular
                  </span>
                )}
                <h3 className="text-lg font-semibold">{p.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold">{p.price}</span>
                  <span className="text-slate-500">{p.period}</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-brand-600" /> {p.docs}
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-brand-600" /> {p.users}
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-brand-600" /> Full verification suite
                  </li>
                </ul>
                <Link
                  href="/register"
                  className={`mt-8 ${p.highlight ? "btn-primary" : "btn-secondary"}`}
                >
                  {p.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-center text-3xl font-bold">Frequently asked questions</h2>
          <div className="mt-10 space-y-4">
            {faqs.map((f) => (
              <details key={f.q} className="card cursor-pointer">
                <summary className="font-semibold">{f.q}</summary>
                <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{f.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-200 py-20 dark:border-slate-800">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold">Ready to stop checking by hand?</h2>
          <p className="mt-3 text-slate-600 dark:text-slate-300">
            Create an account and activate your company license in minutes.
          </p>
          <Link href="/register" className="btn-primary mt-8">
            Get started <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-10 dark:border-slate-800">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
          <p className="text-sm text-slate-500">© 2026 Papery. All rights reserved.</p>
          <div className="flex gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-brand-600">Privacy</a>
            <a href="#" className="hover:text-brand-600">Terms</a>
            <a href="#" className="hover:text-brand-600">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
