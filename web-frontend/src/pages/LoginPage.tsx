import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

interface Props { onSwitchToSignup: () => void; }
type Role = "citizen" | "department";

const LAYERS = [
  { num:"01", title:"Conversational Interface", subtitle:"Chatbot Layer", color:"#3B82F6", icon:"💬",
    tech:["Claude AI","Web Speech API","React + WebSocket"],
    desc:"The citizen-facing layer. Accepts free-text or voice input in Hindi, English, or Hinglish. It is a thin proxy — it does not decide anything, just forwards every message to the state machine.",
    details:["Voice-to-text using browser's Web Speech API (Chrome)","Multi-language: Hindi, English, Hinglish","Post-submission queries handled by Claude AI","Streaming typing indicator while pipeline runs"] },
  { num:"02", title:"State Machine + Slot Filling", subtitle:"NLU / Conversation Control", color:"#8B5CF6", icon:"🧠",
    tech:["Python State Machine","Claude AI (extraction only)","Redis Slots"],
    desc:"The brain of the system. A Python-controlled state machine drives the entire conversation. Claude is used only for slot extraction — the machine decides what to ask next.",
    details:["States: IDLE → INTENT_DISCOVERY → DIAGNOSTIC_Q → LOCATION_CAPTURE → DONE","Diagnostic questions per department category","Duration extraction, multi-domain complaint detection","Completeness checker — all fields verified before routing"] },
  { num:"03", title:"Classification Engine", subtitle:"Department Routing Classifier", color:"#F59E0B", icon:"🏷️",
    tech:["Rule-Based Classifier","MuRIL (Multilingual BERT)","25-Dept Taxonomy"],
    desc:"Maps the complaint to one of 25 government departments using a two-stage approach. Rule-based classifier handles most cases; MuRIL (Google's multilingual BERT for Indian languages) is used as fallback.",
    details:["25 departments: Water, Electricity, Roads, Police, Revenue…","Rule-based first pass with regex word-boundary matching","MuRIL model for ambiguous multilingual cases","Priority: Critical / High / Medium / Low","Sentiment: Neutral / Frustrated / Distressed","Confidence score with clarification retry loop (up to 2×)"] },
  { num:"04", title:"Location Intelligence", subtitle:"Geospatial Layer", color:"#10B981", icon:"📍",
    tech:["Leaflet.js Map","Reverse Geocoding API","SBERT Embeddings"],
    desc:"Processes the citizen's location to determine jurisdiction, ward, pincode, and locality. An interactive map lets citizens drop a pin; GPS auto-fill is also supported.",
    details:["Interactive Leaflet map with drag-to-place pin","GPS browser API for current location","Reverse geocoding → address, ward, pincode, district","SBERT for location similarity deduplication","Determines municipal vs state vs central jurisdiction"] },
  { num:"05", title:"Portal Routing Engine", subtitle:"Jurisdiction & Portal Matching", color:"#EF4444", icon:"🗺️",
    tech:["Rule-Based Router","Portal Registry DB","Jurisdiction Detector"],
    desc:"Given department + location, identifies the correct government portal and selects the matching adapter.",
    details:["Portal registry: Municipal / State / Central levels","Department × location → portal ID lookup","Plug-and-play adapter system — new portals without code change","Returns portal name, API endpoint, required field schema"] },
  { num:"06", title:"Submission Adapter", subtitle:"Portal Integration Layer", color:"#F97316", icon:"📤",
    tech:["Adapter Pattern","Smart Field Pre-fill","Portal-Specific APIs"],
    desc:"Submits the complaint to the identified government portal. Smart pre-fill maps collected conversation data to portal-required fields automatically.",
    details:["Adapter per portal (GenericMock, PGPortal, etc.)","Auto pre-fills: location, description, category, date, contact","Portal-specific ticket ID format (POL/, ELE/, JAL/…)","Returns canonical ticket ID + submission timestamp"] },
  { num:"07", title:"Status Tracker", subtitle:"Real-Time Tracking", color:"#06B6D4", icon:"📡",
    tech:["Redis Pub/Sub","Portal Status APIs","WebSocket Push"],
    desc:"Polls government portals for status changes and pushes updates to the citizen in real time via Redis Pub/Sub events.",
    details:["Periodic polling of portal status endpoints","Status normalization: Pending / In Progress / Resolved / Rejected","Redis Pub/Sub for event-driven pipeline chaining","Live pipeline timeline in the UI right panel","Status change notification injected into chat"] },
];

const ARCH = [
  { label:"Gateway",    port:"8000", desc:"Orchestrator — Redis Pub/Sub pipeline, auth, audit log" },
  { label:"Chatbot",    port:"8001", desc:"Thin proxy, post-submission Claude queries" },
  { label:"Location",   port:"8002", desc:"Geocoding, SBERT deduplication" },
  { label:"NLU",        port:"8003", desc:"State machine, slot filling, Claude extraction" },
  { label:"Classifier", port:"8004", desc:"Rule-based + MuRIL, priority, sentiment" },
  { label:"Routing",    port:"8005", desc:"Portal registry, jurisdiction matching" },
  { label:"Submission", port:"8006", desc:"Adapter pattern, smart field pre-fill" },
  { label:"Tracker",    port:"8007", desc:"Status polling, Redis event push" },
];

function HowItWorksModal({ onClose }: { onClose: () => void }) {
  const [active, setActive] = useState(0);
  const F = { fontFamily:"'Inter',sans-serif" };

  return (
    <div style={{ position:"fixed", inset:0, zIndex:999, display:"flex", alignItems:"flex-start", justifyContent:"center", background:"rgba(0,0,0,0.3)", backdropFilter:"blur(8px)", WebkitBackdropFilter:"blur(8px)", overflowY:"auto", padding:"40px 16px" }}>
      <div style={{ width:"100%", maxWidth:900, background:"rgba(255,255,255,0.95)", backdropFilter:"blur(30px)", WebkitBackdropFilter:"blur(30px)", borderRadius:20, border:"1px solid rgba(0,0,0,0.08)", boxShadow:"0 24px 80px rgba(0,0,0,0.15)", ...F, overflow:"hidden", marginBottom:40 }}>

        {/* Header */}
        <div style={{ padding:"28px 32px 20px", borderBottom:"1px solid #F3F4F6", display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
          <div>
            <p style={{ margin:0, fontSize:"0.6rem", fontWeight:700, letterSpacing:"2px", textTransform:"uppercase", color:"#9CA3AF" }}>SYSTEM ARCHITECTURE</p>
            <h2 style={{ margin:"6px 0 0", fontSize:"1.6rem", fontWeight:600, color:"#111827", letterSpacing:"-0.03em" }}>How Margdarshan.ai Works</h2>
            <p style={{ margin:"6px 0 0", fontSize:"0.82rem", color:"#6B7280", lineHeight:1.5 }}>
              A 7-layer AI pipeline that turns a citizen complaint into a tracked government ticket — in under 60 seconds.
            </p>
          </div>
          <button onClick={onClose}
            style={{ width:32, height:32, borderRadius:"50%", background:"#F3F4F6", border:"1px solid #E5E7EB", color:"#6B7280", fontSize:"1rem", cursor:"pointer", flexShrink:0, display:"flex", alignItems:"center", justifyContent:"center" }}>
            ×
          </button>
        </div>

        <div style={{ display:"flex", minHeight:520 }}>
          {/* Left nav */}
          <div style={{ width:220, borderRight:"1px solid #F3F4F6", padding:"12px", flexShrink:0 }}>
            {LAYERS.map((l, i) => (
              <button key={i} onClick={() => setActive(i)}
                style={{ width:"100%", textAlign:"left", padding:"9px 10px", borderRadius:10, marginBottom:2, border:"none", background: active===i ? l.color+"12" : "transparent", cursor:"pointer", transition:"background 0.12s" }}>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <div style={{ width:26, height:26, borderRadius:8, background: active===i ? l.color+"18" : "#F3F4F6", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"0.8rem", flexShrink:0, border: active===i ? `1px solid ${l.color}30` : "none" }}>
                    {l.icon}
                  </div>
                  <div>
                    <p style={{ margin:0, fontSize:"0.58rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"0.8px", color: active===i ? l.color : "#9CA3AF" }}>{l.num}</p>
                    <p style={{ margin:0, fontSize:"0.71rem", fontWeight:500, color: active===i ? "#111827" : "#6B7280", lineHeight:1.3 }}>{l.title}</p>
                  </div>
                </div>
              </button>
            ))}
            <button onClick={() => setActive(99)}
              style={{ width:"100%", textAlign:"left", padding:"9px 10px", borderRadius:10, marginTop:6, border:"1px solid #E5E7EB", background: active===99 ? "#F9FAFB" : "transparent", cursor:"pointer" }}>
              <p style={{ margin:0, fontSize:"0.58rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"0.8px", color:"#9CA3AF" }}>INFRA</p>
              <p style={{ margin:0, fontSize:"0.71rem", fontWeight:500, color: active===99 ? "#111827" : "#6B7280" }}>Microservices Map</p>
            </button>
          </div>

          {/* Right content */}
          <div style={{ flex:1, padding:"24px 28px", overflowY:"auto" }}>
            {active === 99 ? (
              <div>
                <p style={{ margin:"0 0 4px", fontSize:"0.6rem", fontWeight:700, letterSpacing:"1.5px", textTransform:"uppercase", color:"#9CA3AF" }}>MICROSERVICES OVERVIEW</p>
                <h3 style={{ margin:"0 0 4px", fontSize:"1.2rem", fontWeight:600, color:"#111827", letterSpacing:"-0.02em" }}>8 Independent Services</h3>
                <p style={{ margin:"0 0 18px", fontSize:"0.8rem", color:"#6B7280", lineHeight:1.6 }}>
                  All services communicate via Redis Pub/Sub, orchestrated by the Gateway. Each runs in its own Docker container with health checks.
                </p>
                <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  {ARCH.map((s, i) => (
                    <div key={i} style={{ padding:"10px 14px", borderRadius:12, background:"#F9FAFB", border:"1px solid #E5E7EB", display:"flex", alignItems:"flex-start", gap:12 }}>
                      <span style={{ fontSize:"0.65rem", fontFamily:"monospace", fontWeight:700, color:"#059669", background:"#ECFDF5", padding:"2px 8px", borderRadius:6, flexShrink:0 }}>:{s.port}</span>
                      <div>
                        <p style={{ margin:0, fontSize:"0.82rem", fontWeight:600, color:"#111827" }}>{s.label}</p>
                        <p style={{ margin:"2px 0 0", fontSize:"0.74rem", color:"#6B7280", lineHeight:1.5 }}>{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop:16, padding:"12px 14px", borderRadius:12, background:"#EFF6FF", border:"1px solid #BFDBFE" }}>
                  <p style={{ margin:0, fontSize:"0.75rem", fontWeight:600, color:"#1D4ED8" }}>Event Flow</p>
                  <p style={{ margin:"4px 0 0", fontSize:"0.72rem", color:"#374151", lineHeight:1.7 }}>
                    Chat → Gateway inserts complaint → publishes <code style={{ color:"#059669", background:"#ECFDF5", padding:"1px 5px", borderRadius:4, fontSize:"0.7rem" }}>stage_0_chat</code> → NLU → Classifier → Router → Submission → Tracker. Each stage triggers the next via Redis channel.
                  </p>
                </div>
              </div>
            ) : (() => {
              const l = LAYERS[active];
              return (
                <div>
                  <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:14 }}>
                    <div style={{ width:44, height:44, borderRadius:12, background:l.color+"14", border:`1px solid ${l.color}30`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1.4rem", flexShrink:0 }}>
                      {l.icon}
                    </div>
                    <div>
                      <p style={{ margin:0, fontSize:"0.6rem", fontWeight:700, letterSpacing:"1.5px", textTransform:"uppercase", color:l.color }}>LAYER {l.num}</p>
                      <h3 style={{ margin:0, fontSize:"1.1rem", fontWeight:600, color:"#111827", letterSpacing:"-0.02em" }}>{l.title}</h3>
                      <p style={{ margin:0, fontSize:"0.72rem", color:"#9CA3AF" }}>{l.subtitle}</p>
                    </div>
                  </div>
                  <div style={{ display:"flex", flexWrap:"wrap", gap:5, marginBottom:14 }}>
                    {l.tech.map((t, i) => (
                      <span key={i} style={{ fontSize:"0.68rem", fontWeight:500, padding:"3px 10px", borderRadius:999, background:"#F3F4F6", color:"#374151", border:"1px solid #E5E7EB" }}>{t}</span>
                    ))}
                  </div>
                  <p style={{ fontSize:"0.82rem", color:"#4B5563", lineHeight:1.75, marginBottom:16 }}>{l.desc}</p>
                  <div style={{ background:"#F9FAFB", borderRadius:12, border:"1px solid #E5E7EB", padding:"12px 14px" }}>
                    <p style={{ margin:"0 0 8px", fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF" }}>What it does</p>
                    <div style={{ display:"flex", flexDirection:"column", gap:7 }}>
                      {l.details.map((d, i) => (
                        <div key={i} style={{ display:"flex", gap:10, alignItems:"flex-start" }}>
                          <div style={{ width:5, height:5, borderRadius:"50%", background:l.color, flexShrink:0, marginTop:7 }} />
                          <p style={{ margin:0, fontSize:"0.78rem", color:"#4B5563", lineHeight:1.6 }}>{d}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ display:"flex", gap:8, marginTop:16 }}>
                    {active > 0 && (
                      <button onClick={() => setActive(a => a - 1)}
                        style={{ padding:"8px 18px", borderRadius:999, border:"1px solid #E5E7EB", background:"transparent", color:"#6B7280", fontSize:"0.75rem", cursor:"pointer", fontFamily:"'Inter',sans-serif" }}>
                        ← Previous
                      </button>
                    )}
                    {active < LAYERS.length - 1 && (
                      <button onClick={() => setActive(a => a + 1)}
                        style={{ padding:"8px 18px", borderRadius:999, border:"none", background:l.color, color:"white", fontSize:"0.75rem", fontWeight:600, cursor:"pointer", fontFamily:"'Inter',sans-serif" }}>
                        Next Layer →
                      </button>
                    )}
                    {active === LAYERS.length - 1 && (
                      <button onClick={() => setActive(99)}
                        style={{ padding:"8px 18px", borderRadius:999, border:"1px solid #E5E7EB", background:"transparent", color:"#374151", fontSize:"0.75rem", fontWeight:500, cursor:"pointer", fontFamily:"'Inter',sans-serif" }}>
                        See Infrastructure Map →
                      </button>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
}

export function LoginPage({ onSwitchToSignup }: Props) {
  const { login } = useAuth();
  const [role, setRole] = useState<Role>("citizen");
  const [showForm, setShowForm] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null); setSubmitting(true);
    try { await login(identifier.trim(), password); }
    catch (err: any) { setError(err.message || "Login failed"); }
    finally { setSubmitting(false); }
  };

  const F = { fontFamily:"'Inter',sans-serif" };
  const I: React.CSSProperties = {
    width:"100%", padding:"11px 14px", borderRadius:10,
    border:"1px solid rgba(0,0,0,0.1)", background:"rgba(255,255,255,0.8)",
    fontSize:"0.85rem", color:"#111827", outline:"none", ...F, boxSizing:"border-box",
  };

  return (
    <>
      {showHowItWorks && <HowItWorksModal onClose={() => setShowHowItWorks(false)} />}

      <div style={{ minHeight:"100vh", background:"linear-gradient(135deg, #EDF2F7 0%, #F0F4F9 50%, #EBF0F7 100%)", display:"flex", flexDirection:"column", ...F, position:"relative", overflow:"hidden" }}>

        {/* Subtle light orbs */}
        <div style={{ position:"absolute", width:600, height:600, top:"-20%", right:"-10%", borderRadius:"50%", background:"radial-gradient(circle, rgba(99,102,241,0.07) 0%, transparent 70%)", filter:"blur(60px)", pointerEvents:"none" }} />
        <div style={{ position:"absolute", width:400, height:400, bottom:"-10%", left:"-5%", borderRadius:"50%", background:"radial-gradient(circle, rgba(16,185,129,0.05) 0%, transparent 70%)", filter:"blur(60px)", pointerEvents:"none" }} />

        {/* Nav */}
        <nav style={{ position:"relative", zIndex:10, display:"flex", justifyContent:"space-between", alignItems:"center", padding:"24px 48px" }}>
          <span style={{ fontSize:"1.05rem", fontWeight:700, color:"#111827", letterSpacing:"-0.03em" }}>Margdarshan.ai</span>
          <div style={{ display:"flex", gap:6 }}>
            {(["citizen","department"] as Role[]).map(r => (
              <button key={r} onClick={() => { setRole(r); setShowForm(true); }}
                style={{ padding:"7px 18px", borderRadius:999, border:"1px solid rgba(0,0,0,0.1)", background: role===r && showForm ? "#202A36" : "rgba(255,255,255,0.7)", color: role===r && showForm ? "white" : "#374151", fontSize:"0.78rem", fontWeight:500, cursor:"pointer", ...F, transition:"all 0.15s", backdropFilter:"blur(8px)" }}>
                {r === "citizen" ? "Citizens" : "Department"}
              </button>
            ))}
          </div>
        </nav>

        {/* Hero */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:"0 24px 60px", position:"relative", zIndex:5 }}>

          {!showForm ? (
            <div style={{ textAlign:"center", maxWidth:640 }}>
              <p style={{ fontSize:"0.72rem", fontWeight:600, textTransform:"uppercase", letterSpacing:"2px", color:"#9CA3AF", marginBottom:20 }}>
                AI-POWERED GOVERNMENT GRIEVANCE PORTAL
              </p>
              <h1 style={{ margin:0, lineHeight:0.9, letterSpacing:"-0.04em" }}>
                <span style={{ display:"block", fontSize:"clamp(3rem,8vw,5.5rem)", fontWeight:500, color:"rgba(17,24,39,0.3)" }}>Your Grievance.</span>
                <span style={{ display:"block", fontSize:"clamp(3rem,8vw,5.5rem)", fontWeight:700, color:"#111827", marginTop:"-0.06em" }}>Our Responsibility.</span>
              </h1>
              <p style={{ fontSize:"1rem", color:"#6B7280", lineHeight:1.7, maxWidth:440, margin:"24px auto 0" }}>
                File, track, and resolve government complaints in seconds — in Hindi, English, or Hinglish.
              </p>
              <div style={{ display:"flex", gap:12, justifyContent:"center", marginTop:40 }}>
                <button onClick={() => setShowHowItWorks(true)}
                  style={{ padding:"11px 28px", borderRadius:999, background:"rgba(255,255,255,0.7)", border:"1px solid rgba(0,0,0,0.1)", color:"#374151", fontSize:"0.88rem", fontWeight:500, cursor:"pointer", ...F, backdropFilter:"blur(8px)", transition:"all 0.15s", boxShadow:"0 2px 8px rgba(0,0,0,0.06)" }}
                  onMouseEnter={e => (e.currentTarget.style.background="rgba(255,255,255,0.95)")}
                  onMouseLeave={e => (e.currentTarget.style.background="rgba(255,255,255,0.7)")}>
                  Learn More
                </button>
                <button onClick={() => { setRole("citizen"); setShowForm(true); }}
                  style={{ padding:"11px 28px", borderRadius:999, background:"#202A36", border:"none", color:"white", fontSize:"0.88rem", fontWeight:600, cursor:"pointer", ...F, boxShadow:"0 4px 16px rgba(32,42,54,0.25)", transition:"opacity 0.15s" }}
                  onMouseEnter={e => (e.currentTarget.style.opacity="0.85")}
                  onMouseLeave={e => (e.currentTarget.style.opacity="1")}>
                  File a Complaint →
                </button>
              </div>
            </div>
          ) : (
            <div style={{ width:"100%", maxWidth:400 }}>
              {/* Glass form card */}
              <div style={{ background:"rgba(255,255,255,0.75)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderRadius:20, border:"1px solid rgba(0,0,0,0.07)", boxShadow:"0 8px 32px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.9)", padding:"28px 28px 24px" }}>
                <button onClick={() => setShowForm(false)} style={{ background:"none", border:"none", color:"#9CA3AF", fontSize:"0.78rem", cursor:"pointer", ...F, marginBottom:20, display:"flex", alignItems:"center", gap:5 }}>
                  ← Back
                </button>
                <p style={{ fontSize:"0.62rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.5px", color:"#9CA3AF", marginBottom:6 }}>
                  {role === "citizen" ? "CITIZEN LOGIN" : "DEPARTMENT LOGIN"}
                </p>
                <h2 style={{ fontSize:"1.7rem", fontWeight:700, color:"#111827", letterSpacing:"-0.03em", margin:"0 0 24px" }}>
                  {role === "citizen" ? "Welcome back." : "Dept. Access."}
                </h2>

                <form onSubmit={submit} style={{ display:"flex", flexDirection:"column", gap:12 }}>
                  <div>
                    <label style={{ display:"block", fontSize:"0.72rem", fontWeight:500, color:"#6B7280", marginBottom:5, textTransform:"uppercase", letterSpacing:"0.8px" }}>
                      {role === "citizen" ? "Mobile / Email" : "Official Email"}
                    </label>
                    <input style={I} type="text" value={identifier}
                      placeholder={role === "citizen" ? "9876543210 or email@example.com" : "official@dept.gov.in"}
                      onChange={e => setIdentifier(e.target.value)} required
                      onFocus={e => (e.target.style.borderColor="rgba(32,42,54,0.4)")}
                      onBlur={e => (e.target.style.borderColor="rgba(0,0,0,0.1)")} />
                  </div>
                  <div>
                    <label style={{ display:"block", fontSize:"0.72rem", fontWeight:500, color:"#6B7280", marginBottom:5, textTransform:"uppercase", letterSpacing:"0.8px" }}>Password</label>
                    <div style={{ position:"relative" }}>
                      <input style={{ ...I, paddingRight:52 }} type={showPw ? "text" : "password"}
                        value={password} placeholder="••••••••" onChange={e => setPassword(e.target.value)} required
                        onFocus={e => (e.target.style.borderColor="rgba(32,42,54,0.4)")}
                        onBlur={e => (e.target.style.borderColor="rgba(0,0,0,0.1)")} />
                      <button type="button" onClick={() => setShowPw(s => !s)}
                        style={{ position:"absolute", right:12, top:"50%", transform:"translateY(-50%)", fontSize:"0.7rem", color:"#9CA3AF", background:"none", border:"none", cursor:"pointer", ...F }}>
                        {showPw ? "Hide" : "Show"}
                      </button>
                    </div>
                  </div>
                  {error && <div style={{ fontSize:"0.78rem", color:"#DC2626", background:"#FEF2F2", borderRadius:8, padding:"10px 14px", border:"1px solid #FECACA" }}>{error}</div>}
                  <button type="submit" disabled={submitting}
                    style={{ marginTop:4, padding:"13px", borderRadius:999, border:"none", background: submitting ? "#9CA3AF" : "#202A36", color:"white", fontSize:"0.88rem", fontWeight:700, cursor: submitting ? "default" : "pointer", ...F, letterSpacing:"-0.01em", boxShadow: submitting ? "none" : "0 4px 12px rgba(32,42,54,0.25)" }}>
                    {submitting ? "Signing in…" : role === "citizen" ? "Sign In →" : "Access Dashboard →"}
                  </button>
                </form>

                {role === "citizen" && (
                  <p style={{ textAlign:"center", marginTop:18, fontSize:"0.75rem", color:"#9CA3AF" }}>
                    No account?{" "}
                    <button onClick={onSwitchToSignup} style={{ color:"#202A36", fontWeight:600, background:"none", border:"none", cursor:"pointer", ...F, textDecoration:"underline" }}>
                      Create one
                    </button>
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ position:"relative", zIndex:5, textAlign:"center", padding:"0 24px 24px", fontSize:"0.68rem", color:"#9CA3AF" }}>
          भारत सरकार · Government of India · Ministry of Personnel, Public Grievances &amp; Pensions
        </div>
      </div>
    </>
  );
}
