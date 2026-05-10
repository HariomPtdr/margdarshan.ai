import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import type { RegisterPayload } from "../lib/types";

interface Props {
  onSwitchToLogin: () => void;
}

const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
  "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
  "Uttarakhand", "West Bengal",
];

export function SignupPage({ onSwitchToLogin }: Props) {
  const { register } = useAuth();
  const [form, setForm] = useState<RegisterPayload>({
    name: "",
    gender: "",
    address: "",
    sub_locality: "",
    locality: "",
    country: "India",
    state: "",
    district: "",
    pincode: "",
    mobile: "",
    phone: "",
    email: "",
    password: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof RegisterPayload>(k: K, v: RegisterPayload[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (!/^\d{10}$/.test(form.mobile)) {
      setError("Mobile must be 10 digits");
      return;
    }
    setSubmitting(true);
    try {
      await register(form);
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
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

      <main className="flex-1 max-w-5xl mx-auto w-full p-4 md:p-8">
        <div className="bg-white border border-gray-200 rounded-lg shadow">
          <div className="px-6 py-3 bg-gray-100 border-b border-gray-200">
            <h2 className="text-base font-semibold text-gray-700">Registration / Sign up Form</h2>
          </div>

          <form onSubmit={onSubmit} className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-[#5a1f3d] font-semibold">Enter Details</h3>
              <p className="text-sm text-gray-600">
                Fields marked with <span className="text-red-600">*</span> are mandatory
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
              {/* Left column */}
              <Field label="Name" required>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => set("name", e.target.value)}
                  className={inputCls}
                />
              </Field>

              {/* Right column - gender */}
              <Field label="Gender" required>
                <div className="flex gap-6 px-3 py-2">
                  {["Male", "Female", "Transgender"].map((g) => (
                    <label key={g} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="gender"
                        value={g}
                        checked={form.gender === g}
                        onChange={(e) => set("gender", e.target.value)}
                        required
                      />
                      <span className="text-sm font-semibold">{g}</span>
                    </label>
                  ))}
                </div>
              </Field>

              <Field label="Address" required>
                <input
                  type="text"
                  required
                  placeholder="Premise Number or Name"
                  value={form.address || ""}
                  onChange={(e) => set("address", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Sub-locality">
                <input
                  type="text"
                  placeholder="Sub-locality"
                  value={form.sub_locality || ""}
                  onChange={(e) => set("sub_locality", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Locality">
                <input
                  type="text"
                  placeholder="Locality"
                  value={form.locality || ""}
                  onChange={(e) => set("locality", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Country" required>
                <select
                  required
                  value={form.country || "India"}
                  onChange={(e) => set("country", e.target.value)}
                  className={inputCls}
                >
                  <option value="India">India</option>
                </select>
              </Field>

              <Field label="State" required>
                <select
                  required
                  value={form.state || ""}
                  onChange={(e) => set("state", e.target.value)}
                  className={inputCls}
                >
                  <option value="">--Select a state--</option>
                  {INDIAN_STATES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </Field>

              <Field label="District" required>
                <input
                  type="text"
                  required
                  placeholder="District"
                  value={form.district || ""}
                  onChange={(e) => set("district", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Pincode">
                <input
                  type="text"
                  pattern="\d{6}"
                  maxLength={6}
                  placeholder="6-digit pincode"
                  value={form.pincode || ""}
                  onChange={(e) => set("pincode", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Mobile number" required>
                <input
                  type="tel"
                  required
                  pattern="\d{10}"
                  maxLength={10}
                  placeholder="10-digit mobile"
                  value={form.mobile}
                  onChange={(e) => set("mobile", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Phone number">
                <input
                  type="text"
                  placeholder="Phone number with STD code (e.g. 011XXXXXXX)"
                  value={form.phone || ""}
                  onChange={(e) => set("phone", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="E-mail address" required>
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => set("email", e.target.value)}
                  className={inputCls}
                />
              </Field>

              <Field label="Password" required>
                <input
                  type="password"
                  required
                  minLength={6}
                  placeholder="At least 6 characters"
                  value={form.password}
                  onChange={(e) => set("password", e.target.value)}
                  className={inputCls}
                />
              </Field>
            </div>

            {error && (
              <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 p-3 rounded">
                {error}
              </div>
            )}

            <div className="mt-8 flex items-center justify-between">
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="text-sm text-[#5a1f3d] font-semibold hover:underline"
              >
                Already registered? Login
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2.5 bg-[#1a3a8f] text-white font-semibold rounded hover:bg-[#15306e] disabled:opacity-50 flex items-center gap-2"
              >
                {submitting ? "Submitting..." : "💾 Submit"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

const inputCls =
  "w-full px-3 py-2 bg-white border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-saffron text-sm";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-semibold text-gray-800 mb-1">
        {label}
        {required && <span className="text-red-600"> *</span>}
      </label>
      {children}
    </div>
  );
}
