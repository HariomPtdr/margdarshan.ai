/**
 * AdminApp — Department Dashboard entry point.
 * Accessed at /admin — completely separate from user-facing app.
 * Has its own login using admin credentials (stored in gateway env).
 */

import { LayoutDashboard, Lock, LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { adminStats } from "../lib/api";
import { DashboardPage } from "./DashboardPage";

const GATEWAY = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8000";
const ADMIN_TOKEN_KEY = "shikayat_admin_token";

function getAdminToken(): string | null {
  return sessionStorage.getItem(ADMIN_TOKEN_KEY);
}
function setAdminToken(t: string | null) {
  if (t) sessionStorage.setItem(ADMIN_TOKEN_KEY, t);
  else sessionStorage.removeItem(ADMIN_TOKEN_KEY);
}

async function adminLogin(email: string, password: string): Promise<string> {
  // Reuse the same user auth endpoint — the admin user is a regular account
  // with admin access. For prototype, admin credentials are set during setup.
  const r = await fetch(`${GATEWAY}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier: email, password }),
  });
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(j.detail || "Invalid admin credentials");
  }
  const data = await r.json();
  return data.token as string;
}

async function verifyAdminAccess(token: string): Promise<boolean> {
  // Try to call an admin-only endpoint to verify access
  try {
    await adminStats();
    return true;
  } catch {
    return false;
  }
}

// ── Admin Login Page ────────────────────────────────────────────────────────

function AdminLoginPage({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const token = await adminLogin(email.trim(), password);
      // Temporarily set token so API calls work for verification
      sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
      // Verify admin access by trying an admin endpoint
      const r = await fetch(`${GATEWAY}/api/v1/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) {
        setAdminToken(null);
        throw new Error("Access denied. This account does not have department admin privileges.");
      }
      onLogin(token);
    } catch (err: any) {
      setError(err.message || "Login failed");
      setAdminToken(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-[#1a3a8f] to-gray-900 flex flex-col">
      {/* Gov header */}
      <header className="bg-[#5a1f3d] text-white px-6 py-3">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <div className="text-sm">
            <div>भारत सरकार</div>
            <div className="text-xs opacity-90">Government of India</div>
          </div>
          <div className="text-sm border-l border-white/40 pl-4">
            <div>कार्मिक, लोक शिकायत और पेंशन मंत्रालय</div>
            <div className="text-xs opacity-90">Ministry of Personnel, Public Grievances &amp; Pensions</div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 border border-gray-200">
          {/* Icon + title */}
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 bg-[#1a3a8f] rounded-full flex items-center justify-center mb-3 shadow-lg">
              <LayoutDashboard size={32} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-[#1a3a8f] tracking-wide">DEPARTMENT LOGIN</h1>
            <p className="text-xs text-gray-500 mt-1">Margdarshan.ai — Department Dashboard</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Department Admin Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@department.gov.in"
                required
                className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1a3a8f]"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  required
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1a3a8f] pr-14"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-700"
                >
                  {showPw ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded-lg flex items-start gap-2">
                <Lock size={14} className="mt-0.5 shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-[#1a3a8f] text-white font-semibold rounded-lg hover:bg-[#15306e] disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            >
              <Lock size={16} />
              {loading ? "Signing in..." : "Login to Department Dashboard"}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-gray-100 text-center">
            <a
              href="/"
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              ← Back to citizen portal
            </a>
          </div>
        </div>
      </main>

      <footer className="text-center text-xs text-white/40 py-3">
        Margdarshan.ai — Department Admin Portal · Restricted Access
      </footer>
    </div>
  );
}

// ── Admin App root ──────────────────────────────────────────────────────────

export function AdminApp() {
  const [token, setToken] = useState<string | null>(() => getAdminToken());
  const [verified, setVerified] = useState(false);
  const [checking, setChecking] = useState(!!token);

  // On mount, verify stored token still works
  useEffect(() => {
    if (!token) { setChecking(false); return; }
    verifyAdminAccess(token).then((ok) => {
      if (!ok) { setAdminToken(null); setToken(null); }
      else setVerified(true);
      setChecking(false);
    });
  }, [token]);

  const handleLogin = (t: string) => {
    setAdminToken(t);
    setToken(t);
    setVerified(true);
  };

  const handleLogout = () => {
    setAdminToken(null);
    setToken(null);
    setVerified(false);
  };

  if (checking) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        Verifying admin access...
      </div>
    );
  }

  if (!token || !verified) {
    return <AdminLoginPage onLogin={handleLogin} />;
  }

  // Inject admin token into fetch calls by monkey-patching localStorage
  // (DashboardPage uses authHeaders() which reads localStorage token)
  // We use sessionStorage for admin but DashboardPage reads from localStorage.
  // Simplest: temporarily set localStorage token to admin token while on admin route.
  localStorage.setItem("shikayat_token", token);

  return (
    <div className="h-full flex flex-col">
      {/* Admin top bar */}
      <div className="bg-[#1a3a8f] text-white px-4 py-2 flex items-center justify-between text-sm shrink-0">
        <div className="flex items-center gap-2">
          <LayoutDashboard size={16} />
          <span className="font-semibold">Margdarshan.ai — Department Dashboard</span>
          <span className="text-white/50 text-xs ml-2">· Admin View</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="/" className="text-white/70 hover:text-white text-xs underline">
            Citizen Portal
          </a>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-white/80 hover:text-white text-xs border border-white/30 rounded px-2 py-1 hover:border-white/60 transition-colors"
          >
            <LogOut size={13} /> Logout
          </button>
        </div>
      </div>

      {/* Dashboard content */}
      <div className="flex-1 overflow-hidden">
        <DashboardPage onBack={() => {}} hideBackButton />
      </div>
    </div>
  );
}
