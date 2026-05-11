import type { PipelineState } from "../hooks/usePipeline";
import { useTranslation } from "react-i18next";
import { CheckCircle2, Circle, Loader } from "lucide-react";

interface Props {
  state: PipelineState;
  hasActiveComplaint: boolean;
}

const PRI: Record<string, { color: string; bg: string; border: string }> = {
  Critical: { color:"#DC2626", bg:"#FEF2F2", border:"#FECACA" },
  High:     { color:"#C2410C", bg:"#FFF7ED", border:"#FED7AA" },
  Med:      { color:"#A16207", bg:"#FEFCE8", border:"#FDE68A" },
  Low:      { color:"#15803D", bg:"#F0FDF4", border:"#BBF7D0" },
};

const PIPELINE_STAGES = [
  { key:"stage_0_chat",     label:"Conversation" },
  { key:"stage_1_intake",   label:"Location Confirmed" },
  { key:"stage_2_nlu",      label:"Understanding" },
  { key:"stage_3_classify", label:"Classification" },
  { key:"stage_5_route",    label:"Routing to Dept." },
  { key:"stage_8_submit",   label:"Submitted to Portal" },
];

const F = { fontFamily:"'Inter',sans-serif" };

function GlassCard({ children, style = {} }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background:"rgba(255,255,255,0.75)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderRadius:16, border:"1px solid rgba(255,255,255,0.9)", boxShadow:"0 2px 12px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.9)", overflow:"hidden", ...style }}>
      {children}
    </div>
  );
}

export function RightPanel({ state, hasActiveComplaint }: Props) {
  const { t } = useTranslation();

  if (!hasActiveComplaint) {
    return (
      <aside style={{ height:"100%", display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(255,255,255,0.40)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderLeft:"1px solid rgba(0,0,0,0.06)", ...F, padding:24, textAlign:"center" }}>
        <div>
          <div style={{ width:48, height:48, borderRadius:14, background:"rgba(255,255,255,0.9)", border:"1px solid rgba(0,0,0,0.07)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1.4rem", margin:"0 auto 14px", boxShadow:"0 2px 12px rgba(0,0,0,0.06)" }}>📋</div>
          <p style={{ fontSize:"0.78rem", color:"#9CA3AF", lineHeight:1.7 }}>{t("rightPanel.noActiveComplaint")}</p>
        </div>
      </aside>
    );
  }

  const cls  = state.classification;
  const route = state.routing;
  const sub   = state.submission;
  const loc   = state.location;
  const nlu   = state.nluPayload;
  const pri   = cls?.priority ? (PRI[cls.priority] ?? PRI.Med) : PRI.Med;
  const conf  = cls?.confidence != null && !isNaN(cls.confidence)
    ? Math.round(cls.confidence <= 1 ? cls.confidence * 100 : cls.confidence) : null;

  return (
    <aside style={{ height:"100%", display:"flex", flexDirection:"column", background:"rgba(255,255,255,0.40)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderLeft:"1px solid rgba(0,0,0,0.06)", ...F, overflowY:"auto" }}>

      {/* Sticky header */}
      <div style={{ padding:"14px 16px 12px", borderBottom:"1px solid rgba(0,0,0,0.05)", background:"rgba(255,255,255,0.6)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", position:"sticky", top:0, zIndex:5 }}>
        <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF", margin:0 }}>
          Complaint Details
        </p>
      </div>

      <div style={{ padding:"12px", display:"flex", flexDirection:"column", gap:8 }}>

        {/* Pipeline */}
        <GlassCard>
          <div style={{ padding:"12px 14px 10px", borderBottom:"1px solid rgba(0,0,0,0.04)" }}>
            <span style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF" }}>Pipeline</span>
          </div>
          <div style={{ padding:"10px 14px 14px", display:"flex", flexDirection:"column", gap:0 }}>
            {PIPELINE_STAGES.map((s, i) => {
              const status = state.stages[s.key];
              const done = status === "completed";
              const active = status === "started";
              const isLast = i === PIPELINE_STAGES.length - 1;
              return (
                <div key={s.key} style={{ display:"flex", gap:10, alignItems:"flex-start" }}>
                  <div style={{ display:"flex", flexDirection:"column", alignItems:"center", flexShrink:0 }}>
                    <div style={{ width:22, height:22, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center",
                      background: done ? "#202A36" : active ? "#FFF7ED" : "#F3F4F6",
                      border: active ? "1.5px solid #F97316" : "none",
                      marginTop:6,
                    }}>
                      {done ? <CheckCircle2 size={13} color="white" strokeWidth={2.5} />
                             : active ? <Loader size={12} color="#F97316" className="animate-spin" />
                             : <Circle size={12} color="#D1D5DB" />}
                    </div>
                    {!isLast && (
                      <div style={{ width:1.5, flex:1, minHeight:12, background: done ? "#202A36" : "#E5E7EB", margin:"2px 0" }} />
                    )}
                  </div>
                  <div style={{ paddingBottom: isLast ? 0 : 10, paddingTop:8 }}>
                    <span style={{ fontSize:"0.78rem", fontWeight: done ? 500 : 400, color: done ? "#111827" : active ? "#C2410C" : "#9CA3AF" }}>
                      {s.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>

        {/* Location */}
        {loc && (
          <GlassCard style={{ padding:"12px 14px" }}>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF", marginBottom:8 }}>Location</p>
            <p style={{ fontSize:"0.78rem", color:"#111827", lineHeight:1.55, margin:0 }}>{loc.address_text}</p>
            {(loc.ward || loc.pincode) && (
              <p style={{ fontSize:"0.7rem", color:"#9CA3AF", marginTop:4, margin:"4px 0 0" }}>
                {[loc.ward, loc.pincode].filter(Boolean).join(" · ")}
              </p>
            )}
          </GlassCard>
        )}

        {/* Keywords */}
        {nlu?.keywords?.length > 0 && (
          <GlassCard style={{ padding:"12px 14px" }}>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF", marginBottom:8 }}>Extracted Info</p>
            <div style={{ display:"flex", flexWrap:"wrap", gap:5 }}>
              {nlu.keywords.slice(0, 8).map((k: string) => (
                <span key={k} style={{ fontSize:"0.68rem", fontWeight:500, padding:"3px 10px", borderRadius:999, background:"rgba(255,255,255,0.8)", color:"#374151", border:"1px solid rgba(0,0,0,0.08)" }}>
                  {k}
                </span>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Classification */}
        {cls && (cls.department || cls.priority || conf) && (
          <GlassCard>
            <div style={{ padding:"12px 14px 10px", borderBottom:"1px solid rgba(0,0,0,0.04)" }}>
              <span style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF" }}>Classification</span>
            </div>
            <div style={{ padding:"10px 14px 14px", display:"flex", flexDirection:"column", gap:8 }}>
              {cls.department && (
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                  <span style={{ fontSize:"0.75rem", color:"#6B7280" }}>Department</span>
                  <span style={{ fontSize:"0.75rem", fontWeight:600, color:"#111827", maxWidth:140, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{cls.department}</span>
                </div>
              )}
              {cls.priority && (
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                  <span style={{ fontSize:"0.75rem", color:"#6B7280" }}>Priority</span>
                  <span style={{ fontSize:"0.7rem", fontWeight:700, padding:"2px 10px", borderRadius:999, background:pri.bg, color:pri.color, border:`1px solid ${pri.border}`, display:"flex", alignItems:"center", gap:5 }}>
                    <span style={{ width:5, height:5, borderRadius:"50%", background:pri.color, display:"inline-block" }} />
                    {cls.priority === "Med" ? "Medium" : cls.priority}
                  </span>
                </div>
              )}
              {cls.sentiment && (
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                  <span style={{ fontSize:"0.75rem", color:"#6B7280" }}>Tone</span>
                  <span style={{ fontSize:"0.75rem", fontWeight:500, color:"#374151" }}>{t(`sentiment.${cls.sentiment}`, cls.sentiment)}</span>
                </div>
              )}
              {conf !== null && (
                <div>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                    <span style={{ fontSize:"0.75rem", color:"#6B7280" }}>Confidence</span>
                    <span style={{ fontSize:"0.75rem", fontWeight:700, color: conf >= 80 ? "#15803D" : conf >= 50 ? "#A16207" : "#DC2626" }}>{conf}%</span>
                  </div>
                  <div style={{ height:5, borderRadius:999, background:"#F3F4F6", overflow:"hidden" }}>
                    <div style={{ height:"100%", width:`${conf}%`, borderRadius:999, background: conf >= 80 ? "#202A36" : conf >= 50 ? "#F59E0B" : "#EF4444", transition:"width 0.8s ease" }} />
                  </div>
                </div>
              )}
            </div>
          </GlassCard>
        )}

        {/* Portal */}
        {route && (
          <div style={{ background:"#202A36", borderRadius:16, padding:"14px", boxShadow:"0 4px 16px rgba(32,42,54,0.2)" }}>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"rgba(255,255,255,0.4)", marginBottom:8 }}>Portal</p>
            <p style={{ fontSize:"0.85rem", fontWeight:600, color:"white", lineHeight:1.4, marginBottom:6 }}>{route.portal_name}</p>
            <span style={{ fontSize:"0.68rem", fontWeight:500, padding:"3px 10px", borderRadius:999, background:"rgba(255,255,255,0.12)", color:"rgba(255,255,255,0.75)", textTransform:"capitalize" }}>
              {route.jurisdiction_level}
            </span>
          </div>
        )}

        {/* Submission */}
        {sub && (
          <GlassCard>
            <div style={{ padding:"12px 14px 10px", borderBottom:"1px solid rgba(0,0,0,0.04)", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
              <span style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"#9CA3AF" }}>Status</span>
              <span style={{ fontSize:"0.68rem", fontWeight:700, padding:"2px 10px", borderRadius:999, background:"#F0FDF4", color:"#15803D", border:"1px solid #BBF7D0" }}>
                {sub.canonical_status || "Submitted"}
              </span>
            </div>
            <div style={{ padding:"10px 14px 14px" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:10 }}>
                <span style={{ fontSize:"0.72rem", color:"#6B7280" }}>Ticket ID</span>
                <span style={{ fontSize:"0.72rem", fontWeight:600, color:"#111827", fontFamily:"monospace" }}>{sub.portal_ticket_id || "—"}</span>
              </div>
              <p style={{ fontSize:"0.7rem", color:"#9CA3AF", lineHeight:1.6, margin:0, padding:"8px 10px", background:"rgba(255,255,255,0.7)", borderRadius:8, border:"1px solid rgba(0,0,0,0.05)" }}>
                {t("rightPanel.estimatedResponse")}
              </p>
            </div>
          </GlassCard>
        )}

      </div>
    </aside>
  );
}
