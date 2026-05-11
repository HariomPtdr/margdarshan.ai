import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import type { RegisterPayload } from "../lib/types";

const STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Delhi","Goa","Gujarat",
  "Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra",
  "Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim",
  "Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
];

interface Props { onSwitchToLogin: () => void; }

export function SignupPage({ onSwitchToLogin }: Props) {
  const { register } = useAuth();
  const [form, setForm] = useState<RegisterPayload>({
    name:"", gender:"", address:"", sub_locality:"", locality:"",
    country:"India", state:"", district:"", pincode:"",
    mobile:"", phone:"", email:"", password:"",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof RegisterPayload>(k: K, v: RegisterPayload[K]) =>
    setForm(f => ({ ...f, [k]: v }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null);
    if (form.password.length < 6) { setError("Password must be at least 6 characters"); return; }
    if (!/^\d{10}$/.test(form.mobile)) { setError("Mobile must be 10 digits"); return; }
    setSubmitting(true);
    try { await register(form); }
    catch (err: any) { setError(err.message || "Registration failed"); }
    finally { setSubmitting(false); }
  };

  const F = { fontFamily:"'Inter',sans-serif" };
  const I: React.CSSProperties = {
    width:"100%", padding:"11px 14px", borderRadius:10,
    border:"1px solid rgba(0,0,0,0.09)", background:"rgba(255,255,255,0.85)",
    fontSize:"0.85rem", color:"#111827", outline:"none", ...F, boxSizing:"border-box" as any,
  };
  const S: React.CSSProperties = { ...I };

  return (
    <div style={{ minHeight:"100vh", background:"linear-gradient(135deg, #EDF2F7 0%, #F0F4F9 50%, #EBF0F7 100%)", ...F, display:"flex", flexDirection:"column", position:"relative", overflow:"hidden" }}>
      {/* Subtle orbs */}
      <div style={{ position:"absolute", width:500, height:500, top:"-10%", right:"-5%", borderRadius:"50%", background:"radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)", filter:"blur(60px)", pointerEvents:"none" }} />
      <div style={{ position:"absolute", width:400, height:400, bottom:"-5%", left:"-8%", borderRadius:"50%", background:"radial-gradient(circle, rgba(16,185,129,0.05) 0%, transparent 70%)", filter:"blur(60px)", pointerEvents:"none" }} />

      {/* Nav */}
      <nav style={{ position:"relative", zIndex:10, display:"flex", justifyContent:"space-between", alignItems:"center", padding:"22px 48px", background:"rgba(255,255,255,0.6)", backdropFilter:"blur(16px)", WebkitBackdropFilter:"blur(16px)", borderBottom:"1px solid rgba(0,0,0,0.06)" }}>
        <span style={{ fontSize:"1.05rem", fontWeight:700, color:"#111827", letterSpacing:"-0.03em" }}>Margdarshan.ai</span>
        <button onClick={onSwitchToLogin}
          style={{ padding:"7px 20px", borderRadius:999, border:"none", background:"#202A36", color:"white", fontSize:"0.78rem", fontWeight:600, cursor:"pointer", ...F, boxShadow:"0 2px 8px rgba(32,42,54,0.2)" }}>
          Sign In
        </button>
      </nav>

      {/* Form */}
      <div style={{ flex:1, display:"flex", justifyContent:"center", padding:"32px 24px 48px", position:"relative", zIndex:5, overflowY:"auto" }}>
        <div style={{ width:"100%", maxWidth:640 }}>
          {/* Heading */}
          <div style={{ marginBottom:32 }}>
            <p style={{ fontSize:"0.65rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"2px", color:"#9CA3AF", margin:"0 0 10px" }}>CREATE ACCOUNT</p>
            <h1 style={{ margin:0, letterSpacing:"-0.04em", lineHeight:0.9 }}>
              <span style={{ display:"block", fontSize:"clamp(2rem,5vw,3.5rem)", fontWeight:500, color:"rgba(17,24,39,0.25)" }}>Join.</span>
              <span style={{ display:"block", fontSize:"clamp(2rem,5vw,3.5rem)", fontWeight:700, color:"#111827", marginTop:"-0.05em" }}>File. Track.</span>
            </h1>
          </div>

          {/* Glass form card */}
          <div style={{ background:"rgba(255,255,255,0.75)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderRadius:20, border:"1px solid rgba(0,0,0,0.07)", boxShadow:"0 8px 32px rgba(0,0,0,0.07), inset 0 1px 0 rgba(255,255,255,0.9)", padding:"28px 28px 24px" }}>
            <form onSubmit={onSubmit} style={{ display:"flex", flexDirection:"column", gap:0 }}>

              <Sec label="Personal Details">
                <Row2>
                  <F2 label="Full Name" required>
                    <input style={I} type="text" required value={form.name} placeholder="Your full name" onChange={e => set("name", e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                  <F2 label="Gender" required>
                    <div style={{ display:"flex", gap:16, paddingTop:10 }}>
                      {["Male","Female","Transgender"].map(g => (
                        <label key={g} style={{ display:"flex", alignItems:"center", gap:6, cursor:"pointer", fontSize:"0.82rem", color:"#374151", fontWeight:500 }}>
                          <input type="radio" name="gender" value={g} checked={form.gender===g} onChange={e => set("gender",e.target.value)} required style={{ accentColor:"#202A36" }} />
                          {g}
                        </label>
                      ))}
                    </div>
                  </F2>
                </Row2>
              </Sec>

              <Sec label="Contact">
                <Row2>
                  <F2 label="Mobile" required>
                    <input style={I} type="tel" required pattern="\d{10}" maxLength={10} value={form.mobile} placeholder="10-digit mobile" onChange={e => set("mobile",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                  <F2 label="Email" required>
                    <input style={I} type="email" required value={form.email} placeholder="you@example.com" onChange={e => set("email",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                </Row2>
              </Sec>

              <Sec label="Address">
                <Row2>
                  <F2 label="Street Address" required>
                    <input style={I} type="text" required value={form.address||""} placeholder="House / Building / Street" onChange={e => set("address",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                  <F2 label="Locality">
                    <input style={I} type="text" value={form.locality||""} placeholder="Locality / Colony" onChange={e => set("locality",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                  <F2 label="State" required>
                    <select style={S} required value={form.state||""} onChange={e => set("state",e.target.value)} onFocus={focus} onBlur={blur}>
                      <option value="">Select state</option>
                      {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </F2>
                  <F2 label="District" required>
                    <input style={I} type="text" required value={form.district||""} placeholder="District" onChange={e => set("district",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                  <F2 label="Pincode">
                    <input style={I} type="text" pattern="\d{6}" maxLength={6} value={form.pincode||""} placeholder="6-digit pincode" onChange={e => set("pincode",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                </Row2>
              </Sec>

              <Sec label="Security">
                <Row2>
                  <F2 label="Password" required>
                    <input style={I} type="password" required minLength={6} value={form.password} placeholder="At least 6 characters" onChange={e => set("password",e.target.value)} onFocus={focus} onBlur={blur} />
                  </F2>
                </Row2>
              </Sec>

              {error && (
                <div style={{ fontSize:"0.8rem", color:"#DC2626", background:"#FEF2F2", borderRadius:10, padding:"12px 16px", marginTop:4, border:"1px solid #FECACA" }}>{error}</div>
              )}

              <div style={{ marginTop:24, display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                <button type="button" onClick={onSwitchToLogin}
                  style={{ fontSize:"0.8rem", color:"#9CA3AF", background:"none", border:"none", cursor:"pointer", ...F, textDecoration:"underline" }}>
                  Already registered? Sign in
                </button>
                <button type="submit" disabled={submitting}
                  style={{ padding:"12px 32px", borderRadius:999, border:"none", background: submitting ? "#9CA3AF" : "#202A36", color:"white", fontSize:"0.88rem", fontWeight:700, cursor: submitting ? "default" : "pointer", ...F, letterSpacing:"-0.01em", boxShadow: submitting ? "none" : "0 4px 12px rgba(32,42,54,0.25)" }}>
                  {submitting ? "Creating account…" : "Create Account →"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ position:"relative", zIndex:5, textAlign:"center", padding:"0 24px 20px", fontSize:"0.65rem", color:"#9CA3AF" }}>
        भारत सरकार · Government of India · Ministry of Personnel, Public Grievances &amp; Pensions
      </div>
    </div>
  );
}

function focus(e: React.FocusEvent<HTMLInputElement|HTMLSelectElement>) {
  e.target.style.borderColor = "rgba(32,42,54,0.35)";
}
function blur(e: React.FocusEvent<HTMLInputElement|HTMLSelectElement>) {
  e.target.style.borderColor = "rgba(0,0,0,0.09)";
}

function Sec({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom:24 }}>
      <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", marginBottom:14, borderTop:"1px solid rgba(0,0,0,0.06)", paddingTop:18 }}>{label}</p>
      {children}
    </div>
  );
}

function Row2({ children }: { children: React.ReactNode }) {
  return <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>{children}</div>;
}

function F2({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ display:"block", fontSize:"0.68rem", fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px", color:"#6B7280", marginBottom:6 }}>
        {label}{required && <span style={{ color:"#EF4444", marginLeft:3 }}>*</span>}
      </label>
      {children}
    </div>
  );
}
