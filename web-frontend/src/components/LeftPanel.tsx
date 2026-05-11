import { Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { ComplaintSummary } from "../lib/types";

interface Props {
  complaints: ComplaintSummary[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; dot: string }> = {
  resolved:    { label: "Resolved",    color: "#15803D", bg: "#F0FDF4", dot: "#22c55e" },
  submitted:   { label: "Submitted",   color: "#1D4ED8", bg: "#EFF6FF", dot: "#3b82f6" },
  in_progress: { label: "In Progress", color: "#C2410C", bg: "#FFF7ED", dot: "#f97316" },
  rejected:    { label: "Rejected",    color: "#B91C1C", bg: "#FEF2F2", dot: "#ef4444" },
  active:      { label: "Active",      color: "#6B7280", bg: "#F9FAFB", dot: "#D1D5DB" },
  pending:     { label: "Active",      color: "#6B7280", bg: "#F9FAFB", dot: "#D1D5DB" },
};

export function LeftPanel({ complaints, activeId, onSelect, onNew }: Props) {
  const { t } = useTranslation();

  return (
    <aside style={{ height:"100%", display:"flex", flexDirection:"column", background:"rgba(255,255,255,0.65)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderRight:"1px solid rgba(0,0,0,0.07)", fontFamily:"'Inter',sans-serif" }}>

      {/* Title */}
      <div style={{ padding:"14px 14px 10px", borderBottom:"1px solid rgba(0,0,0,0.06)" }}>
        <span style={{ fontSize:"0.58rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.5px", color:"#9CA3AF" }}>
          {t("leftPanel.title")}
        </span>
      </div>

      {/* List */}
      <div style={{ flex:1, overflowY:"auto", padding:"8px" }}>
        {complaints.length === 0 && (
          <div style={{ fontSize:"0.75rem", color:"#9CA3AF", padding:"24px 8px", textAlign:"center", lineHeight:1.7 }}>
            {t("leftPanel.noComplaints")}
          </div>
        )}
        {complaints.map((c) => {
          const cfg = STATUS_CONFIG[c.status] ?? STATUS_CONFIG.active;
          const isActive = c.complaint_id === activeId;
          return (
            <button key={c.complaint_id} onClick={() => onSelect(c.complaint_id)}
              style={{
                width:"100%", textAlign:"left", padding:"10px 12px", borderRadius:12, marginBottom:4,
                border: isActive ? "1.5px solid rgba(32,42,54,0.25)" : "1px solid rgba(0,0,0,0.06)",
                background: isActive ? "rgba(32,42,54,0.06)" : "rgba(255,255,255,0.6)",
                backdropFilter:"blur(8px)", WebkitBackdropFilter:"blur(8px)",
                cursor:"pointer", transition:"all 0.12s",
                boxShadow: isActive ? "0 2px 8px rgba(0,0,0,0.08)" : "0 1px 3px rgba(0,0,0,0.04)",
              }}
              onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = "rgba(255,255,255,0.85)"; e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.08)"; } }}
              onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = "rgba(255,255,255,0.6)"; e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.04)"; } }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:4 }}>
                <span style={{ fontSize:"0.72rem", fontWeight:600, color:"#111827", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap", maxWidth:"60%" }}>
                  {c.department || "Complaint"}
                </span>
                <span style={{ fontSize:"0.6rem", fontWeight:600, padding:"2px 8px", borderRadius:999, background:cfg.bg, color:cfg.color, display:"flex", alignItems:"center", gap:4 }}>
                  <span style={{ width:4, height:4, borderRadius:"50%", background:cfg.dot, display:"inline-block" }} />
                  {cfg.label}
                </span>
              </div>
              <p style={{ fontSize:"0.7rem", color:"#6B7280", lineHeight:1.45, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical", overflow:"hidden", margin:0 }}>
                {c.summary}
              </p>
              {c.ticket_id && (
                <p style={{ fontSize:"0.6rem", marginTop:4, fontFamily:"monospace", color:"#9CA3AF", margin:"4px 0 0" }}>
                  #{c.ticket_id}
                </p>
              )}
            </button>
          );
        })}
      </div>

      {/* New complaint */}
      <div style={{ padding:"10px 8px", borderTop:"1px solid rgba(0,0,0,0.06)" }}>
        <button onClick={onNew}
          style={{ width:"100%", display:"flex", alignItems:"center", justifyContent:"center", gap:7, padding:"11px", borderRadius:999, background:"#202A36", border:"none", color:"white", fontSize:"0.78rem", fontWeight:600, cursor:"pointer", letterSpacing:"-0.01em", fontFamily:"'Inter',sans-serif", transition:"all 0.15s", boxShadow:"0 2px 8px rgba(32,42,54,0.2)" }}
          onMouseEnter={e => { e.currentTarget.style.background="#2d3b4e"; }}
          onMouseLeave={e => { e.currentTarget.style.background="#202A36"; }}>
          <Plus size={14} />
          {t("leftPanel.newComplaint")}
        </button>
      </div>
    </aside>
  );
}
