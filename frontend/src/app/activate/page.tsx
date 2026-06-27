"use client";

import { KeyRound, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthShell } from "@/components/auth-shell";
import { useAuth } from "@/lib/auth";

const DEMO_KEYS = [
  "PAPERY-FREE-DEMO-2026",
  "PAPERY-PRO-DEMO-2026",
  "PAPERY-ENT-DEMO-2026",
];

export default function ActivatePage() {
  const router = useRouter();
  const { user, loading, activate, logout } = useAuth();
  const [licenseKey, setLicenseKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
    } else if (user.role === "SUPER_ADMIN" || user.license?.status === "ACTIVE") {
      router.replace("/dashboard");
    }
  }, [user, loading, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await activate(licenseKey);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Activation failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  const isAdmin = user.role === "ADMIN";

  return (
    <AuthShell
      title="Activate your license"
      subtitle={`Welcome, ${user.full_name}. Enter your company license key to continue.`}
    >
      {!isAdmin ? (
        <div className="space-y-4 text-center">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Your company license is not active yet. Please ask your company
            administrator to activate it.
          </p>
          <button onClick={logout} className="btn-secondary w-full">
            <LogOut className="h-4 w-4" /> Log out
          </button>
        </div>
      ) : (
        <>
          <form onSubmit={onSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
                {error}
              </div>
            )}
            <div>
              <label className="label" htmlFor="key">License key</label>
              <div className="relative">
                <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  id="key"
                  required
                  className="input pl-9 font-mono uppercase"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  placeholder="PAPERY-XXXX-XXXX"
                />
              </div>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? "Activating…" : "Activate"}
            </button>
          </form>

          <div className="mt-6 rounded-lg border border-dashed border-slate-300 p-4 text-xs dark:border-slate-700">
            <p className="font-semibold text-slate-600 dark:text-slate-300">
              Demo license keys (development):
            </p>
            <ul className="mt-2 space-y-1">
              {DEMO_KEYS.map((k) => (
                <li key={k}>
                  <button
                    type="button"
                    onClick={() => setLicenseKey(k)}
                    className="font-mono text-brand-600 hover:underline"
                  >
                    {k}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <button onClick={logout} className="btn-secondary mt-4 w-full">
            <LogOut className="h-4 w-4" /> Log out
          </button>
        </>
      )}
    </AuthShell>
  );
}
