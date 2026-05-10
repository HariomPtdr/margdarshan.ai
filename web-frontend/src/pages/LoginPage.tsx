import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

interface Props {
  onSwitchToSignup: () => void;
}

export function LoginPage({ onSwitchToSignup }: Props) {
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(identifier.trim(), password);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-saffron/10 via-white to-govgreen/10 flex flex-col">
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
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8 border border-gray-200">
          <h1 className="text-2xl font-bold text-[#1a3a8f] tracking-wide mb-6">USER LOGIN</h1>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Mobile No / Email Id
              </label>
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="Mobile No / Email Id"
                required
                className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-saffron"
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
                  className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-saffron pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500"
                >
                  {showPw ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {error && <div className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-[#1a3a8f] text-white font-semibold rounded hover:bg-[#15306e] disabled:opacity-50"
            >
              {submitting ? "Signing in..." : "Login →"}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-gray-200 text-center text-sm text-gray-700">
            <button
              type="button"
              onClick={onSwitchToSignup}
              className="text-[#5a1f3d] font-semibold hover:underline"
            >
              Click here to sign up
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
