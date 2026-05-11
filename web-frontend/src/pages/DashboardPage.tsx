import {
  Activity,
  AlertCircle,
  ArrowLeft,
  BarChart2,
  Building2,
  CheckCircle,
  ChevronRight,
  Clock,
  Copy,
  ExternalLink,
  FileText,
  Globe,
  Hash,
  MapPin,
  Phone,
  Shield,
  ThumbsDown,
  ThumbsUp,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  adminComplaintDetail,
  adminComplaints,
  adminPortalDetail,
  adminPortals,
  adminStats,
  reviewComplaint,
  updateComplaintStatus,
} from "../lib/api";
import type { ReviewPayload } from "../lib/api";
import type {
  AdminComplaintDetail,
  AdminComplaintRow,
  AdminPortal,
  AdminStats,
} from "../lib/types";
import { DemoTracePage } from "./DemoTracePage";

const DEPARTMENTS = [
  "ELECTRICITY", "WATER", "ROADS", "SANITATION", "HEALTH", "EDUCATION",
  "TRANSPORT", "REVENUE", "POLICE", "MUNICIPAL", "PWD", "AGRICULTURE",
  "SOCIAL_WELFARE", "HOUSING", "TELECOM", "BANKING", "POSTAL",
  "ENVIRONMENT", "LABOUR", "FOOD_SUPPLY",
];

// ── helpers ──────────────────────────────────────────────────────────

function fmt(ts: number) {
  return new Date(ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

function statusColor(s: string) {
  const m: Record<string, string> = {
    active: "bg-blue-100 text-blue-700",
    submitted: "bg-yellow-100 text-yellow-700",
    pending: "bg-yellow-100 text-yellow-700",
    in_progress: "bg-orange-100 text-orange-700",
    resolved: "bg-green-100 text-green-700",
    rejected: "bg-red-100 text-red-700",
    failed: "bg-red-100 text-red-700",
  };
  return m[s?.toLowerCase()] ?? "bg-gray-100 text-gray-600";
}

function levelBadge(level: string) {
  const m: Record<string, string> = {
    Regional: "bg-purple-100 text-purple-700",
    State: "bg-blue-100 text-blue-700",
    Central: "bg-indigo-100 text-indigo-700",
  };
  return m[level] ?? "bg-gray-100 text-gray-600";
}

function Badge({ label, color }: { label: string; color: string }) {
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>{label}</span>;
}

// ── Stats overview ────────────────────────────────────────────────────

function StatsView({ stats, onPortals, onComplaints }: { stats: AdminStats; onPortals: () => void; onComplaints: () => void }) {
  const statusMap = Object.fromEntries(stats.by_status.map((s) => [s.status, s.count]));
  const F = { fontFamily:"'Inter',sans-serif" };
  const deptIcon = (d: string) => d?.includes("ELECT") ? "⚡" : d?.includes("WATER") ? "💧" : d?.includes("POLICE") ? "🚔" : d?.includes("ROAD") ? "🛣️" : d?.includes("HEALTH") ? "🏥" : d?.includes("SANIT") ? "🗑️" : "📋";
  const SC: Record<string,{bg:string;text:string}> = { submitted:{bg:"#EFF6FF",text:"#1D4ED8"}, resolved:{bg:"#F0FDF4",text:"#15803D"}, active:{bg:"#F9FAFB",text:"#6B7280"}, in_progress:{bg:"#FFF7ED",text:"#C2410C"}, rejected:{bg:"#FEF2F2",text:"#DC2626"} };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14, ...F }}>

      {/* ── Hero metric banner ── */}
      <div style={{ background:"#202A36", borderRadius:20, padding:"24px 28px", position:"relative", overflow:"hidden" }}>
        {/* Subtle pattern */}
        <div style={{ position:"absolute", inset:0, backgroundImage:"radial-gradient(circle at 80% 50%, rgba(255,255,255,0.04) 0%, transparent 60%), radial-gradient(circle at 20% 100%, rgba(255,255,255,0.03) 0%, transparent 50%)", pointerEvents:"none" }} />
        <div style={{ position:"relative", zIndex:1, display:"grid", gridTemplateColumns:"2fr 1fr 1fr 1fr", gap:0 }}>
          {/* Main metric */}
          <div style={{ borderRight:"1px solid rgba(255,255,255,0.1)", paddingRight:28 }}>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.5px", color:"rgba(255,255,255,0.35)", margin:"0 0 10px" }}>Total Complaints</p>
            <p style={{ fontSize:"3.5rem", fontWeight:700, color:"white", margin:"0 0 6px", letterSpacing:"-0.06em", lineHeight:1 }}>{stats.total_complaints}</p>
            <p style={{ fontSize:"0.72rem", color:"rgba(255,255,255,0.35)", margin:0, fontWeight:500 }}>All time · across all departments</p>
          </div>
          {/* Secondary metrics */}
          {[
            { label:"Submitted",   value:statusMap["submitted"]??0,  color:"#93C5FD", sub:"Awaiting" },
            { label:"Resolved",    value:statusMap["resolved"]??0,   color:"#86EFAC", sub:"Closed" },
            { label:"Duplicates",  value:stats.duplicate_complaints, color:"#FED7AA", sub:"Grouped" },
          ].map(m => (
            <div key={m.label} style={{ paddingLeft:24, display:"flex", flexDirection:"column", justifyContent:"center" }}>
              <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"rgba(255,255,255,0.3)", margin:"0 0 8px" }}>{m.label}</p>
              <p style={{ fontSize:"2rem", fontWeight:700, color:m.color, margin:"0 0 4px", letterSpacing:"-0.04em", lineHeight:1 }}>{m.value}</p>
              <p style={{ fontSize:"0.65rem", color:"rgba(255,255,255,0.25)", margin:0 }}>{m.sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Charts + Activity ── */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:14 }}>

        {/* Departments */}
        <div style={{ background:"white", borderRadius:18, boxShadow:"0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)", padding:"20px 22px" }}>
          <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:"0 0 18px" }}>By Department</p>
          {stats.by_department.slice(0,6).map(({ department, count }) => {
            const pct = Math.min(100, (count/(stats.total_complaints||1))*100);
            return (
              <div key={department} style={{ marginBottom:14 }}>
                <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:5 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:7 }}>
                    <span style={{ fontSize:"0.8rem" }}>{deptIcon(department)}</span>
                    <span style={{ fontSize:"0.75rem", color:"#374151", fontWeight:500 }}>{department}</span>
                  </div>
                  <span style={{ fontSize:"0.78rem", fontWeight:700, color:"#111827" }}>{count}</span>
                </div>
                <div style={{ height:5, background:"#F3F4F6", borderRadius:999, overflow:"hidden" }}>
                  <div style={{ height:"100%", width:`${pct}%`, background:"#202A36", borderRadius:999 }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Districts */}
        <div style={{ background:"white", borderRadius:18, boxShadow:"0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)", padding:"20px 22px" }}>
          <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:"0 0 18px" }}>By District</p>
          {stats.by_district.slice(0,6).map(({ district, count }) => {
            const pct = Math.min(100, (count/(stats.total_complaints||1))*100);
            return (
              <div key={district} style={{ marginBottom:14 }}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                  <span style={{ fontSize:"0.75rem", color:"#374151", fontWeight:500 }}>📍 {district}</span>
                  <span style={{ fontSize:"0.78rem", fontWeight:700, color:"#111827" }}>{count}</span>
                </div>
                <div style={{ height:5, background:"#F3F4F6", borderRadius:999, overflow:"hidden" }}>
                  <div style={{ height:"100%", width:`${pct}%`, background:"#3B82F6", borderRadius:999 }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Recent Activity */}
        <div style={{ background:"white", borderRadius:18, boxShadow:"0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)", overflow:"hidden", display:"flex", flexDirection:"column" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"16px 18px 12px", borderBottom:"1px solid #F3F4F6", flexShrink:0 }}>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:0 }}>Recent</p>
            <button onClick={onComplaints} style={{ fontSize:"0.72rem", fontWeight:600, color:"#202A36", background:"none", border:"none", cursor:"pointer", display:"flex", alignItems:"center", gap:3, ...F }}>
              All <ChevronRight size={11} />
            </button>
          </div>
          <div style={{ flex:1, overflowY:"auto" }}>
            {stats.recent.slice(0,8).map((c, i) => {
              const sc = SC[c.status] ?? SC.active;
              return (
                <div key={c.complaint_id} style={{ display:"flex", alignItems:"center", gap:10, padding:"9px 16px", borderBottom: i<7 ? "1px solid #F9FAFB" : "none", transition:"background 0.1s", cursor:"default" }}
                  onMouseEnter={e => (e.currentTarget.style.background="#F9FAFB")}
                  onMouseLeave={e => (e.currentTarget.style.background="transparent")}>
                  <span style={{ fontSize:"0.8rem", flexShrink:0 }}>{deptIcon(c.department||"")}</span>
                  <div style={{ flex:1, minWidth:0 }}>
                    <p style={{ fontSize:"0.75rem", fontWeight:500, color:"#111827", margin:"0 0 2px", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{c.summary}</p>
                    <p style={{ fontSize:"0.62rem", color:"#9CA3AF", margin:0 }}>{fmt(c.created_at)}</p>
                  </div>
                  <span style={{ fontSize:"0.6rem", fontWeight:700, padding:"2px 7px", borderRadius:999, background:sc.bg, color:sc.text, flexShrink:0, whiteSpace:"nowrap" }}>
                    {c.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Quick nav ── */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
        <button onClick={onPortals}
          style={{ background:"white", borderRadius:16, boxShadow:"0 2px 10px rgba(0,0,0,0.05)", border:"1.5px solid transparent", padding:"16px 20px", display:"flex", alignItems:"center", gap:14, cursor:"pointer", textAlign:"left", ...F, transition:"all 0.15s" }}
          onMouseEnter={e => { e.currentTarget.style.borderColor="#202A36"; e.currentTarget.style.boxShadow="0 4px 16px rgba(0,0,0,0.10)"; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor="transparent"; e.currentTarget.style.boxShadow="0 2px 10px rgba(0,0,0,0.05)"; }}>
          <div style={{ width:42, height:42, borderRadius:13, background:"#F3F4F6", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1.3rem" }}>🏛️</div>
          <div>
            <p style={{ fontSize:"0.9rem", fontWeight:600, color:"#111827", margin:"0 0 3px", letterSpacing:"-0.01em" }}>Portal Registry</p>
            <p style={{ fontSize:"0.72rem", color:"#9CA3AF", margin:0 }}>Browse 70+ government portals</p>
          </div>
          <ChevronRight size={16} style={{ marginLeft:"auto", color:"#D1D5DB" }} />
        </button>
        <button onClick={onComplaints}
          style={{ background:"#202A36", borderRadius:16, boxShadow:"0 4px 16px rgba(32,42,54,0.35)", border:"none", padding:"16px 20px", display:"flex", alignItems:"center", gap:14, cursor:"pointer", textAlign:"left", ...F, transition:"all 0.15s", position:"relative", overflow:"hidden" }}>
          <div style={{ position:"absolute", inset:0, backgroundImage:"radial-gradient(circle at 90% 50%, rgba(255,255,255,0.05), transparent 60%)", pointerEvents:"none" }} />
          <div style={{ width:42, height:42, borderRadius:13, background:"rgba(255,255,255,0.12)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1.3rem", position:"relative" }}>📋</div>
          <div style={{ position:"relative" }}>
            <p style={{ fontSize:"0.9rem", fontWeight:600, color:"white", margin:"0 0 3px", letterSpacing:"-0.01em" }}>All Complaints</p>
            <p style={{ fontSize:"0.72rem", color:"rgba(255,255,255,0.4)", margin:0 }}>{stats.total_complaints} total · review & manage</p>
          </div>
          <ChevronRight size={16} style={{ marginLeft:"auto", color:"rgba(255,255,255,0.25)", position:"relative" }} />
        </button>
      </div>
    </div>
  );
}

// ── Portal list ───────────────────────────────────────────────────────

function PortalListView({ portals, onSelect }: { portals: AdminPortal[]; onSelect: (id: string) => void }) {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("All");
  const F = { fontFamily:"'Inter',sans-serif" };

  const filtered = portals.filter((p) => {
    const q = search.toLowerCase();
    const matchSearch = !q || p.portal_name.toLowerCase().includes(q) || p.authority_name.toLowerCase().includes(q);
    const matchLevel = levelFilter === "All" || p.portal_level === levelFilter;
    return matchSearch && matchLevel;
  });

  // Level → color accent (top strip on card)
  const LC: Record<string,{strip:string;badge:string;badgeText:string}> = {
    Regional: { strip:"#7C3AED", badge:"#EDE9FE", badgeText:"#7C3AED" },
    State:    { strip:"#2563EB", badge:"#DBEAFE", badgeText:"#1D4ED8" },
    Central:  { strip:"#202A36", badge:"#E5E7EB", badgeText:"#374151" },
  };
  const def = { strip:"#9CA3AF", badge:"#F3F4F6", badgeText:"#6B7280" };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14, ...F }}>

      {/* Search + filters */}
      <div style={{ display:"flex", gap:10, alignItems:"center" }}>
        <div style={{ flex:1, position:"relative" }}>
          <svg style={{ position:"absolute", left:14, top:"50%", transform:"translateY(-50%)", color:"#9CA3AF" }} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input
            style={{ width:"100%", padding:"11px 16px 11px 38px", borderRadius:14, border:"none", background:"white", fontSize:"0.85rem", outline:"none", ...F, boxSizing:"border-box", color:"#111827", boxShadow:"0 2px 8px rgba(0,0,0,0.06)" }}
            placeholder="Search portals by name or authority…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div style={{ display:"flex", gap:4, background:"white", borderRadius:12, padding:"4px", boxShadow:"0 2px 8px rgba(0,0,0,0.06)" }}>
          {["All","Regional","State","Central"].map(l => (
            <button key={l} onClick={() => setLevelFilter(l)}
              style={{ padding:"6px 16px", borderRadius:9, border:"none", fontSize:"0.75rem", fontWeight:500, cursor:"pointer", ...F, transition:"all 0.12s",
                background: levelFilter===l ? "#202A36" : "transparent",
                color: levelFilter===l ? "white" : "#6B7280",
              }}>
              {l}
            </button>
          ))}
        </div>
      </div>

      <p style={{ fontSize:"0.7rem", color:"#9CA3AF", fontWeight:500 }}>{filtered.length} portals</p>

      {/* Card grid */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))", gap:12 }}>
        {filtered.map((p) => {
          const lc = LC[p.portal_level] ?? def;
          const hasComplaints = p.complaint_count > 0;
          return (
            <button key={p.portal_id} onClick={() => onSelect(p.portal_id)}
              style={{ background:"white", borderRadius:16, border:"none", padding:0, textAlign:"left", cursor:"pointer", display:"flex", flexDirection:"column", ...F, overflow:"hidden", boxShadow:"0 2px 10px rgba(0,0,0,0.06)", transition:"all 0.15s" }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow="0 8px 24px rgba(0,0,0,0.12)"; e.currentTarget.style.transform="translateY(-2px)"; }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow="0 2px 10px rgba(0,0,0,0.06)"; e.currentTarget.style.transform="translateY(0)"; }}>

              {/* Colored top strip */}
              <div style={{ height:3, background:lc.strip, width:"100%" }} />

              <div style={{ padding:"14px 16px", flex:1, display:"flex", flexDirection:"column", gap:10 }}>
                {/* Count + icon row */}
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
                  <div style={{ width:38, height:38, borderRadius:11, background:"#F3F4F6", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1.1rem" }}>🏛️</div>
                  <div style={{ textAlign:"right" }}>
                    <p style={{ fontSize:hasComplaints ? "2rem" : "1.4rem", fontWeight:700, color: hasComplaints ? "#111827" : "#D1D5DB", margin:0, letterSpacing:"-0.04em", lineHeight:1 }}>{p.complaint_count}</p>
                    <p style={{ fontSize:"0.6rem", color:"#9CA3AF", margin:"3px 0 0" }}>complaints</p>
                </div>
              </div>
              {/* Portal name */}
              <div>
                <p style={{ fontSize:"0.87rem", fontWeight:600, color:"#111827", margin:"0 0 3px", lineHeight:1.35 }}>{p.portal_name}</p>
                <p style={{ fontSize:"0.7rem", color:"#9CA3AF", margin:0, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{p.authority_name}</p>
              </div>
              {/* Footer badges */}
              <div style={{ display:"flex", alignItems:"center", gap:5, paddingTop:6, borderTop:"1px solid #F3F4F6", marginTop:"auto" }}>
                <span style={{ fontSize:"0.62rem", fontWeight:700, padding:"3px 8px", borderRadius:999, background:lc.badge, color:lc.badgeText }}>{p.portal_level}</span>
                {p.has_online && (
                  <span style={{ fontSize:"0.62rem", fontWeight:700, padding:"3px 8px", borderRadius:999, background:"#F0FDF4", color:"#15803D" }}>● Online</span>
                )}
                {p.helpline && (
                  <span style={{ fontSize:"0.6rem", color:"#C4C9D4", marginLeft:"auto", display:"flex", alignItems:"center", gap:2 }}>
                    <Phone size={8}/>{p.helpline}
                  </span>
                )}
              </div>
            </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Portal detail ─────────────────────────────────────────────────────

function PortalDetailView({
  portalId,
  onComplaint,
}: {
  portalId: string;
  onComplaint: (id: string) => void;
}) {
  const [data, setData] = useState<{ portal: AdminPortal; complaints: AdminComplaintRow[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminPortalDetail(portalId).then(setData).finally(() => setLoading(false));
  }, [portalId]);

  if (loading) return <p className="text-center text-gray-400 py-12">Loading…</p>;
  if (!data) return <p className="text-center text-red-400 py-12">Failed to load portal.</p>;

  const { portal, complaints } = data;

  const FP = { fontFamily:"'Inter',sans-serif" };
  const lvlStrip: Record<string,string> = { Regional:"#7C3AED", State:"#2563EB", Central:"#202A36" };
  const strip = lvlStrip[portal.portal_level] ?? "#9CA3AF";
  const SCP: Record<string,{bg:string;text:string}> = { submitted:{bg:"#EFF6FF",text:"#1D4ED8"}, resolved:{bg:"#F0FDF4",text:"#15803D"}, active:{bg:"#F9FAFB",text:"#6B7280"}, in_progress:{bg:"#FFF7ED",text:"#C2410C"}, rejected:{bg:"#FEF2F2",text:"#DC2626"} };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14, ...FP }}>

      {/* Portal header */}
      <div style={{ background:"white", borderRadius:18, overflow:"hidden", boxShadow:"0 2px 12px rgba(0,0,0,0.07)" }}>
        <div style={{ height:4, background:strip }} />
        <div style={{ padding:"20px 24px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12 }}>
            <div style={{ flex:1 }}>
              <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:5, flexWrap:"wrap" }}>
                <h2 style={{ fontSize:"1.1rem", fontWeight:700, color:"#111827", margin:0, letterSpacing:"-0.02em" }}>{portal.portal_name}</h2>
                <span style={{ fontSize:"0.65rem", fontWeight:700, padding:"3px 9px", borderRadius:999, background: portal.portal_level==="Regional"?"#EDE9FE":portal.portal_level==="State"?"#DBEAFE":"#E5E7EB", color: portal.portal_level==="Regional"?"#7C3AED":portal.portal_level==="State"?"#1D4ED8":"#374151" }}>
                  {portal.portal_level}
                </span>
              </div>
              <p style={{ fontSize:"0.8rem", color:"#6B7280", margin:0 }}>{portal.authority_name}</p>
            </div>
            <a href={portal.website} target="_blank" rel="noreferrer"
              style={{ display:"flex", alignItems:"center", gap:5, fontSize:"0.75rem", fontWeight:600, color:"#202A36", textDecoration:"none", padding:"7px 14px", borderRadius:999, border:"1.5px solid #E5E7EB", flexShrink:0 }}>
              <ExternalLink size={12} /> Visit Portal
            </a>
          </div>
          <div style={{ display:"flex", gap:24, marginTop:16, paddingTop:14, borderTop:"1px solid #F3F4F6", alignItems:"center" }}>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <span style={{ fontSize:"1.8rem", fontWeight:700, color:"#111827", letterSpacing:"-0.04em" }}>{portal.complaint_count}</span>
              <span style={{ fontSize:"0.68rem", color:"#9CA3AF", lineHeight:1.4 }}>complaints<br/>routed</span>
            </div>
            {portal.helpline && <div style={{ display:"flex", alignItems:"center", gap:5, color:"#6B7280", fontSize:"0.78rem" }}><Phone size={12}/>{portal.helpline}</div>}
            {portal.has_online && <span style={{ fontSize:"0.65rem", fontWeight:700, padding:"3px 9px", borderRadius:999, background:"#F0FDF4", color:"#15803D", marginLeft:"auto" }}>● Online</span>}
          </div>
          {portal.classifier_dept_tags?.length > 0 && (
            <div style={{ display:"flex", gap:5, flexWrap:"wrap", marginTop:12 }}>
              {portal.classifier_dept_tags.slice(0,8).map(t => <span key={t} style={{ fontSize:"0.62rem", padding:"2px 8px", borderRadius:999, background:"#F3F4F6", color:"#6B7280" }}>{t}</span>)}
            </div>
          )}
        </div>
      </div>

      {/* Complaints list */}
      <div style={{ background:"white", borderRadius:18, boxShadow:"0 2px 12px rgba(0,0,0,0.07)", overflow:"hidden" }}>
        <div style={{ padding:"12px 20px 10px", borderBottom:"1px solid #F3F4F6" }}>
          <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:0 }}>Complaints ({data.total})</p>
        </div>
        {complaints.length === 0 ? (
          <p style={{ textAlign:"center", color:"#9CA3AF", padding:"40px 0", fontSize:"0.85rem" }}>No complaints routed to this portal yet.</p>
        ) : (
          <div>
            {complaints.map((c, ci) => {
              const scp = SCP[c.status] ?? SCP.active;
              return (
              <button
                key={c.complaint_id}
                onClick={() => onComplaint(c.complaint_id)}
                style={{ width:"100%", textAlign:"left", padding:"12px 20px", borderBottom: ci<complaints.length-1?"1px solid #F9FAFB":"none", display:"flex", alignItems:"center", gap:12, background:"none", border:"none", cursor:"pointer", fontFamily:"'Inter',sans-serif", transition:"background 0.1s" }}
                onMouseEnter={e => (e.currentTarget.style.background="#F9FAFB")}
                onMouseLeave={e => (e.currentTarget.style.background="transparent")}
              >
                <div style={{ flex:1, minWidth:0 }}>
                  <p style={{ fontSize:"0.82rem", fontWeight:500, color:"#111827", margin:"0 0 3px", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{c.summary}</p>
                  <div style={{ display:"flex", gap:6, fontSize:"0.68rem", color:"#9CA3AF" }}>
                    <span>{c.user_name}</span>
                    {c.district && <><span>·</span><span>{c.district}</span></>}
                    {c.ticket_id && <span style={{ fontFamily:"monospace", color:"#3B82F6" }}>{c.ticket_id}</span>}
                  </div>
                </div>
                <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:4, flexShrink:0 }}>
                  <span style={{ fontSize:"0.65rem", fontWeight:700, padding:"2px 9px", borderRadius:999, background:scp.bg, color:scp.text }}>{c.status}</span>
                  <span style={{ fontSize:"0.65rem", color:"#9CA3AF" }}>{fmt(c.created_at)}</span>
                </div>
                <ChevronRight size={14} style={{ color:"#D1D5DB", flexShrink:0 }} />
              </button>
            );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Toast notification ────────────────────────────────────────────────

function Toast({ message, type, onDismiss }: { message: string; type: "success" | "error"; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [onDismiss]);
  return (
    <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 ${
      type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
    }`}>
      {type === "success" ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
      {message}
    </div>
  );
}

// ── Review Form ───────────────────────────────────────────────────────

function ReviewForm({
  complaintId,
  currentDept,
  onSuccess,
}: {
  complaintId: string;
  currentDept?: string;
  onSuccess: () => void;
}) {
  const [classificationCorrect, setClassificationCorrect] = useState<boolean | null>(null);
  const [correctDept, setCorrectDept] = useState(currentDept || "");
  const [correctSubCat, setCorrectSubCat] = useState("");
  const [priorityCorrect, setPriorityCorrect] = useState<boolean | null>(null);
  const [correctPriority, setCorrectPriority] = useState("");
  const [sentimentCorrect, setSentimentCorrect] = useState<boolean | null>(null);
  const [rating, setRating] = useState<"positive" | "negative" | null>(null);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (rating === null) { setError("Please select an overall rating."); return; }
    setError("");
    setSubmitting(true);
    try {
      const payload: ReviewPayload = {
        rating,
        reviewer_notes: notes || undefined,
      };
      if (classificationCorrect !== null) payload.classification_correct = classificationCorrect;
      if (!classificationCorrect && correctDept) payload.correct_department = correctDept;
      if (!classificationCorrect && correctSubCat) payload.correct_sub_category = correctSubCat;
      if (priorityCorrect !== null) {
        // we store priority_correct in sentiment_correct field for now; use classification_correct path
      }
      if (priorityCorrect === false && correctPriority) payload.correct_priority = correctPriority;
      if (sentimentCorrect !== null) payload.sentiment_correct = sentimentCorrect;
      await reviewComplaint(complaintId, payload);
      onSuccess();
    } catch (e: any) {
      setError(e.message || "Failed to submit review.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border p-4 space-y-4">
      <h3 className="font-semibold text-gray-800 flex items-center gap-2">
        <Shield size={15} className="text-blue-500" /> Review Classification
      </h3>

      {/* Classification correct? */}
      <div>
        <p className="text-sm text-gray-600 mb-2">Was AI classification correct?</p>
        <div className="flex gap-2">
          {[true, false].map((v) => (
            <button
              key={String(v)}
              onClick={() => setClassificationCorrect(v)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                classificationCorrect === v
                  ? v ? "bg-green-600 text-white" : "bg-red-500 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {v ? "Yes" : "No"}
            </button>
          ))}
        </div>
      </div>

      {/* Correct department/sub-category — shown if classification wrong */}
      {classificationCorrect === false && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Correct Department</label>
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={correctDept}
              onChange={(e) => setCorrectDept(e.target.value)}
            >
              <option value="">Select department…</option>
              {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Correct Sub-Category</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              placeholder="e.g. POWER_OUTAGE"
              value={correctSubCat}
              onChange={(e) => setCorrectSubCat(e.target.value)}
            />
          </div>
        </div>
      )}

      {/* Priority correct? */}
      <div>
        <p className="text-sm text-gray-600 mb-2">Was priority correct?</p>
        <div className="flex gap-2">
          {[true, false].map((v) => (
            <button
              key={String(v)}
              onClick={() => setPriorityCorrect(v)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                priorityCorrect === v
                  ? v ? "bg-green-600 text-white" : "bg-red-500 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {v ? "Yes" : "No"}
            </button>
          ))}
        </div>
        {priorityCorrect === false && (
          <div className="mt-2">
            <label className="text-xs text-gray-500 mb-1 block">Correct Priority</label>
            <select
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={correctPriority}
              onChange={(e) => setCorrectPriority(e.target.value)}
            >
              <option value="">Select…</option>
              {["Low", "Medium", "High", "Critical"].map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        )}
      </div>

      {/* Sentiment correct? */}
      <div>
        <p className="text-sm text-gray-600 mb-2">Was sentiment analysis correct?</p>
        <div className="flex gap-2">
          {[true, false].map((v) => (
            <button
              key={String(v)}
              onClick={() => setSentimentCorrect(v)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                sentimentCorrect === v
                  ? v ? "bg-green-600 text-white" : "bg-red-500 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {v ? "Yes" : "No"}
            </button>
          ))}
        </div>
      </div>

      {/* Overall rating */}
      <div>
        <p className="text-sm text-gray-600 mb-2">Overall rating</p>
        <div className="flex gap-3">
          <button
            onClick={() => setRating("positive")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
              rating === "positive" ? "bg-green-50 border-green-500 text-green-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <ThumbsUp size={16} /> Positive
          </button>
          <button
            onClick={() => setRating("negative")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
              rating === "negative" ? "bg-red-50 border-red-500 text-red-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <ThumbsDown size={16} /> Negative
          </button>
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="text-xs text-gray-500 mb-1 block">Notes (optional)</label>
        <textarea
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
          rows={2}
          placeholder="Additional observations…"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {submitting ? "Submitting…" : "Submit Review"}
      </button>
    </div>
  );
}

// ── Status Changer ────────────────────────────────────────────────────

function StatusChanger({
  complaintId,
  currentStatus,
  onSuccess,
}: {
  complaintId: string;
  currentStatus: string;
  onSuccess: (newStatus: string) => void;
}) {
  const [selected, setSelected] = useState(currentStatus);
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleConfirm() {
    setLoading(true);
    setError("");
    try {
      await updateComplaintStatus(complaintId, selected);
      setConfirming(false);
      onSuccess(selected);
    } catch (e: any) {
      setError(e.message || "Failed to update status.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ background:"white", borderRadius:16, boxShadow:"0 2px 12px rgba(0,0,0,0.07)", padding:"18px 20px", fontFamily:"'Inter',sans-serif" }}>
      <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:"0 0 14px" }}>Update Status</p>
      <div style={{ display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" }}>
        <select value={selected} onChange={(e) => { setSelected(e.target.value); setConfirming(false); }}
          style={{ padding:"9px 14px", borderRadius:10, border:"1.5px solid #E5E7EB", background:"#F9FAFB", fontSize:"0.83rem", color:"#111827", outline:"none", fontFamily:"'Inter',sans-serif", cursor:"pointer" }}>
          {["pending","in_progress","resolved","rejected"].map(s => (
            <option key={s} value={s}>{s.replace("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}</option>
          ))}
        </select>
        {!confirming ? (
          <button onClick={() => setConfirming(true)} disabled={selected===currentStatus}
            style={{ padding:"9px 22px", borderRadius:999, border:"none", background: selected===currentStatus ? "#E5E7EB" : "#202A36", color: selected===currentStatus ? "#9CA3AF" : "white", fontSize:"0.83rem", fontWeight:600, cursor: selected===currentStatus ? "default" : "pointer", fontFamily:"'Inter',sans-serif", transition:"all 0.15s" }}>
            Update Status
          </button>
        ) : (
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ fontSize:"0.8rem", color:"#374151" }}>Confirm → <strong>{selected}</strong>?</span>
            <button onClick={handleConfirm} disabled={loading}
              style={{ padding:"7px 16px", borderRadius:999, border:"none", background:"#15803D", color:"white", fontSize:"0.78rem", fontWeight:600, cursor:"pointer", fontFamily:"'Inter',sans-serif" }}>
              {loading ? "…" : "Confirm"}
            </button>
            <button onClick={() => setConfirming(false)}
              style={{ padding:"7px 14px", borderRadius:999, border:"1px solid #E5E7EB", background:"white", color:"#374151", fontSize:"0.78rem", fontWeight:500, cursor:"pointer", fontFamily:"'Inter',sans-serif" }}>
              Cancel
            </button>
          </div>
        )}
      </div>
      {error && <p style={{ fontSize:"0.75rem", color:"#DC2626", marginTop:8 }}>{error}</p>}
    </div>
  );
}

// ── Complaint detail ──────────────────────────────────────────────────

function DetailStatusBadge({ status }: { status: string }) {
  const m: Record<string, { bg: string; text: string }> = {
    submitted:   { bg:"rgba(59,130,246,0.2)",  text:"#93C5FD" },
    resolved:    { bg:"rgba(34,197,94,0.2)",   text:"#86EFAC" },
    active:      { bg:"rgba(255,255,255,0.1)", text:"rgba(255,255,255,0.6)" },
    in_progress: { bg:"rgba(249,115,22,0.2)",  text:"#FED7AA" },
    rejected:    { bg:"rgba(239,68,68,0.2)",   text:"#FCA5A5" },
  };
  const sc = m[status] ?? m.active;
  return (
    <span style={{ fontSize:"0.7rem", fontWeight:700, padding:"3px 12px", borderRadius:999, background:sc.bg, color:sc.text, flexShrink:0, fontFamily:"'Inter',sans-serif" }}>
      {status}
    </span>
  );
}

function ComplaintDetailView({ complaintId }: { complaintId: string }) {
  const [detail, setDetail] = useState<AdminComplaintDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAudit, setShowAudit] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [showTrace, setShowTrace] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  function loadDetail() {
    setLoading(true);
    adminComplaintDetail(complaintId).then(setDetail).finally(() => setLoading(false));
  }

  useEffect(() => {
    loadDetail();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [complaintId]);

  if (loading) return <p className="text-center text-gray-400 py-12">Loading…</p>;
  if (!detail) return <p className="text-center text-red-400 py-12">Complaint not found.</p>;

  const cls = detail.pipeline.classification;
  const pf  = detail.pipeline.portal_fields;
  const sub = detail.pipeline.submission;

  function maskMobile(mobile: string): string {
    if (!mobile || mobile.length < 4) return "****";
    return "*".repeat(mobile.length - 4) + mobile.slice(-4);
  }

  function maskAadhaar(): string {
    return "****-****-****";
  }

  return (
    <div className="space-y-4">
      {toast && (
        <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />
      )}

      {/* Header */}
      <div style={{ background:"#202A36", borderRadius:16, padding:"20px 22px", fontFamily:"'Inter',sans-serif" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12 }}>
          <div style={{ flex:1 }}>
            <p style={{ fontSize:"0.62rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1px", color:"rgba(255,255,255,0.35)", margin:"0 0 8px" }}>
              Complaint #{detail.complaint_id.slice(0,8).toUpperCase()}
            </p>
            <p style={{ fontSize:"1rem", fontWeight:600, color:"white", margin:0, lineHeight:1.4 }}>{detail.summary || "Complaint"}</p>
          </div>
          <DetailStatusBadge status={detail.status} />
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12, marginTop:16 }}>
          {[["Filed by", detail.filer.name],["Mobile", maskMobile(detail.filer.mobile)],["District", detail.district||"—"],["Filed", fmt(detail.created_at)]].map(([l,v]) => (
            <div key={l}>
              <p style={{ fontSize:"0.62rem", color:"rgba(255,255,255,0.35)", margin:"0 0 4px", fontWeight:600, textTransform:"uppercase", letterSpacing:"0.8px" }}>{l}</p>
              <p style={{ fontSize:"0.82rem", color:"white", margin:0, fontWeight:500 }}>{v}</p>
            </div>
          ))}
        </div>
      </div>

        {detail.ticket_id && (
          <div style={{ marginTop:10, padding:"12px 14px", background:"white", borderRadius:12, border:"1px solid #E5E7EB", display:"flex", alignItems:"center", justifyContent:"space-between", fontFamily:"'Inter',sans-serif" }}>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <Hash size={13} style={{ color:"#22c55e" }} />
              <span style={{ fontSize:"0.82rem", fontFamily:"monospace", fontWeight:600, color:"#15803D" }}>{detail.ticket_id}</span>
              <span style={{ fontSize:"0.68rem", color:"#9CA3AF" }}>Portal ticket</span>
            </div>
            <button onClick={() => setShowTrace(true)}
              style={{ fontSize:"0.72rem", background:"#202A36", color:"white", padding:"5px 12px", borderRadius:999, border:"none", cursor:"pointer", fontFamily:"'Inter',sans-serif", fontWeight:500, display:"flex", alignItems:"center", gap:5 }}>
              🔌 API Trace
            </button>
          </div>
        )}

        {/* Demo trace overlay */}
        {showTrace && (
          <div className="fixed inset-0 z-50">
            <DemoTracePage
              complaintId={detail.complaint_id}
              onBack={() => setShowTrace(false)}
            />
          </div>
        )}

      {/* Status Change */}
      <StatusChanger
        complaintId={detail.complaint_id}
        currentStatus={detail.status}
        onSuccess={(newStatus) => {
          setDetail((d) => d ? { ...d, status: newStatus } : d);
          setToast({ message: `Status updated to "${newStatus}"`, type: "success" });
        }}
      />

      {/* Classification */}
      {cls && (
        <div style={{ background:"white", borderRadius:16, boxShadow:"0 2px 12px rgba(0,0,0,0.07)", padding:"18px 20px", fontFamily:"'Inter',sans-serif" }}>
          <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:"0 0 14px" }}>Classification</p>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12, marginBottom:14 }}>
            {[["Department",cls.department],["Sub-category",cls.sub_category],["Priority",cls.priority],["Sentiment",cls.sentiment]].map(([k,v]) => {
              const isPriority = k === "Priority";
              const priColor = v==="Critical"?"#DC2626":v==="High"?"#C2410C":v==="Med"?"#A16207":"#15803D";
              const priBg = v==="Critical"?"#FEF2F2":v==="High"?"#FFF7ED":v==="Med"?"#FEFCE8":"#F0FDF4";
              return (
                <div key={k}>
                  <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"0.8px", color:"#9CA3AF", margin:"0 0 5px" }}>{k}</p>
                  {isPriority && v ? (
                    <span style={{ fontSize:"0.75rem", fontWeight:700, padding:"3px 10px", borderRadius:999, background:priBg, color:priColor }}>{v}</span>
                  ) : (
                    <p style={{ fontSize:"0.85rem", fontWeight:600, color:"#111827", margin:0 }}>{v || "—"}</p>
                  )}
                </div>
              );
            })}
          </div>
          {cls.confidence !== undefined && (
            <div>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                <span style={{ fontSize:"0.7rem", color:"#9CA3AF", fontWeight:500 }}>Confidence</span>
                <span style={{ fontSize:"0.75rem", fontWeight:700, color:"#111827" }}>{Math.round(cls.confidence*100)}%</span>
              </div>
              <div style={{ height:6, background:"#F3F4F6", borderRadius:999, overflow:"hidden" }}>
                <div style={{ height:"100%", width:`${Math.round(cls.confidence*100)}%`, background:"#202A36", borderRadius:999 }} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Routing Decision */}
      {detail.routing_explanation && (
        <div style={{ background:"#202A36", borderRadius:16, padding:"18px 20px", position:"relative", overflow:"hidden", fontFamily:"'Inter',sans-serif" }}>
          <div style={{ position:"absolute", inset:0, backgroundImage:"radial-gradient(circle at 90% 50%, rgba(255,255,255,0.04), transparent 60%)", pointerEvents:"none" }} />
          <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"rgba(255,255,255,0.35)", margin:"0 0 10px", position:"relative" }}>Routing Decision</p>
          <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:8, position:"relative" }}>
            <span style={{ fontSize:"1rem", fontWeight:700, color:"white", letterSpacing:"-0.01em" }}>{detail.routing_explanation.portal_name}</span>
            <span style={{ fontSize:"0.65rem", fontWeight:700, padding:"3px 9px", borderRadius:999, background:"rgba(255,255,255,0.12)", color:"rgba(255,255,255,0.7)" }}>{detail.routing_explanation.level}</span>
          </div>
          <p style={{ fontSize:"0.78rem", color:"rgba(255,255,255,0.45)", margin:0, lineHeight:1.5, position:"relative" }}>{detail.routing_explanation.reason}</p>
        </div>
      )}

      {/* Collected Portal Fields */}
      {pf && Object.keys(pf).length > 0 && (
        <div style={{ background:"white", borderRadius:16, boxShadow:"0 2px 12px rgba(0,0,0,0.07)", overflow:"hidden", fontFamily:"'Inter',sans-serif" }}>
          <div style={{ padding:"14px 20px 12px", borderBottom:"1px solid #F3F4F6" }}>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.2px", color:"#9CA3AF", margin:0 }}>Collected Portal Fields</p>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:0 }}>
            {Object.entries(pf).map(([k,v],i) => (
              <div key={k} style={{ padding:"12px 20px", borderBottom: i < Object.keys(pf).length-2 ? "1px solid #F9FAFB" : "none", borderRight: i%2===0 ? "1px solid #F9FAFB" : "none" }}>
                <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"0.8px", color:"#9CA3AF", margin:"0 0 4px" }}>{k}</p>
                <p style={{ fontSize:"0.83rem", fontWeight:600, color:"#111827", margin:0, wordBreak:"break-all" }}>{v as string}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Duplicate Filers Panel */}
      {detail.dedup.is_duplicate && !detail.dedup.is_same_user && detail.dedup.duplicate_count > 0 && (
        <div className="bg-orange-50 rounded-xl border border-orange-200 p-4">
          <h3 className="font-semibold text-orange-800 mb-3 flex items-center gap-2">
            <Users size={15} /> {detail.dedup.duplicate_count} Other User(s) Filed the Same Complaint
          </h3>
          <div className="space-y-3">
            {detail.dedup.duplicate_filers.map((f) => (
              <div key={f.complaint_id} className="bg-white rounded-lg border border-orange-100 p-3">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-medium text-gray-800">{f.name}</span>
                    <span className="text-xs text-gray-500 ml-2 font-mono">
                      {maskMobile(f.mobile)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {f.similarity !== undefined && f.similarity > 0 && (
                      <span className="text-xs text-orange-600">{Math.round(f.similarity * 100)}% match</span>
                    )}
                    <Badge label={f.status} color={statusColor(f.status)} />
                  </div>
                </div>
                <p className="text-xs text-gray-400">
                  Aadhaar: <span className="font-mono">{maskAadhaar()}</span>
                  {" · "}Filed: {new Date(f.filed_at).toLocaleString("en-IN")}
                </p>
                {Object.keys(f.portal_fields).length > 0 && (
                  <div className="mt-2 grid grid-cols-2 gap-1">
                    {Object.entries(f.portal_fields).map(([k, v]) => (
                      <div key={k} className="text-xs">
                        <span className="text-gray-400">{k}: </span>
                        <span className="text-gray-700">{v}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Submission */}
      {sub && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2"><CheckCircle size={15} className="text-green-600" /> Submission</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><p className="text-xs text-gray-400">Ticket ID</p><p className="font-mono text-sm">{sub.portal_ticket_id || "—"}</p></div>
            <div><p className="text-xs text-gray-400">Portal Status</p><p className="font-medium">{sub.portal_status_raw || "—"}</p></div>
            <div><p className="text-xs text-gray-400">Submitted At</p><p className="font-medium">{sub.submitted_at ? new Date(sub.submitted_at).toLocaleString("en-IN") : "—"}</p></div>
            <div><p className="text-xs text-gray-400">Adapter</p><p className="font-medium">{sub.adapter || "—"}</p></div>
          </div>
          {sub.portal_url && (
            <a href={sub.portal_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline">
              <ExternalLink size={12} /> View on portal
            </a>
          )}
        </div>
      )}

      {/* Audit chain */}
      {detail.audit_chain.length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <button
            className="w-full flex items-center justify-between font-semibold text-gray-800"
            onClick={() => setShowAudit((v) => !v)}
          >
            <span className="flex items-center gap-2"><Shield size={15} /> Audit Trail ({detail.audit_chain.length} events)</span>
            <ChevronRight size={14} className={`transition-transform ${showAudit ? "rotate-90" : ""}`} />
          </button>
          {showAudit && (
            <div className="mt-3 space-y-2">
              {detail.audit_chain.map((e) => (
                <div key={e.event_id} className="border-l-2 border-gray-200 pl-3 py-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700">{e.event_type}</span>
                    <span className="text-xs text-gray-400">by {e.actor}</span>
                    <span className="text-xs text-gray-400">{new Date(e.created_at).toLocaleString("en-IN")}</span>
                  </div>
                  <p className="text-xs font-mono text-gray-400 truncate">#{e.event_hash.slice(0, 16)}…</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Review Panel */}
      <div className="bg-white rounded-xl border p-4">
        <button
          className="w-full flex items-center justify-between font-semibold text-gray-800"
          onClick={() => setShowReview((v) => !v)}
        >
          <span className="flex items-center gap-2"><ThumbsUp size={15} className="text-blue-500" /> Submit Classification Review</span>
          <ChevronRight size={14} className={`transition-transform ${showReview ? "rotate-90" : ""}`} />
        </button>
        {showReview && (
          <div className="mt-4">
            <ReviewForm
              complaintId={detail.complaint_id}
              currentDept={detail.department}
              onSuccess={() => {
                setShowReview(false);
                setToast({ message: "Review submitted successfully!", type: "success" });
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Complaints list ───────────────────────────────────────────────────

function ComplaintsListView({ onSelect }: { onSelect: (id: string) => void }) {
  const [data, setData] = useState<{ complaints: AdminComplaintRow[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    setLoading(true);
    adminComplaints({ status: statusFilter || undefined, limit: 100 })
      .then(setData)
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const F = { fontFamily:"'Inter',sans-serif" };
  const SC: Record<string,{bg:string;text:string}> = {
    submitted:   {bg:"#EFF6FF",text:"#1D4ED8"},
    resolved:    {bg:"#F0FDF4",text:"#15803D"},
    active:      {bg:"#F9FAFB",text:"#6B7280"},
    in_progress: {bg:"#FFF7ED",text:"#C2410C"},
    rejected:    {bg:"#FEF2F2",text:"#DC2626"},
  };

  const statusColors: Record<string,string> = { active:"#60A5FA", submitted:"#93C5FD", in_progress:"#FED7AA", resolved:"#86EFAC", rejected:"#FCA5A5" };
  const totalByStatus = data ? Object.fromEntries(["active","submitted","in_progress","resolved","rejected"].map(s => [s, (data.complaints ?? []).filter(c => c.status===s).length])) : {};

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:12, ...F }}>

      {/* Header banner */}
      <div style={{ background:"#202A36", borderRadius:18, padding:"20px 24px", position:"relative", overflow:"hidden" }}>
        <div style={{ position:"absolute", inset:0, backgroundImage:"radial-gradient(circle at 80% 50%, rgba(255,255,255,0.04), transparent 60%)", pointerEvents:"none" }} />
        <div style={{ position:"relative", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
          <div>
            <p style={{ fontSize:"0.6rem", fontWeight:700, textTransform:"uppercase", letterSpacing:"1.5px", color:"rgba(255,255,255,0.35)", margin:"0 0 6px" }}>All Complaints</p>
            <p style={{ fontSize:"2.8rem", fontWeight:700, color:"white", margin:0, letterSpacing:"-0.05em", lineHeight:1 }}>{data?.total ?? "…"}</p>
          </div>
          <div style={{ display:"flex", gap:16 }}>
            {[["submitted","Submitted"],["resolved","Resolved"],["in_progress","In Progress"]].map(([k,l]) => (
              <div key={k} style={{ textAlign:"center" }}>
                <p style={{ fontSize:"1.4rem", fontWeight:700, color: statusColors[k] ?? "white", margin:"0 0 2px", letterSpacing:"-0.03em", lineHeight:1 }}>{totalByStatus[k] ?? 0}</p>
                <p style={{ fontSize:"0.6rem", color:"rgba(255,255,255,0.3)", margin:0, fontWeight:500 }}>{l}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filter tabs — floating white pill */}
      <div style={{ background:"white", borderRadius:14, boxShadow:"0 2px 10px rgba(0,0,0,0.06)", padding:"5px", display:"flex", gap:3, alignSelf:"flex-start" }}>
        {[["","All"],["active","Active"],["submitted","Submitted"],["in_progress","In Progress"],["resolved","Resolved"],["rejected","Rejected"]].map(([v,l]) => (
          <button key={v} onClick={() => setStatusFilter(v)}
            style={{ padding:"6px 14px", borderRadius:10, border:"none", fontSize:"0.75rem", fontWeight:statusFilter===v ? 600 : 500, cursor:"pointer", ...F, transition:"all 0.12s",
              background: statusFilter===v ? "#202A36" : "transparent",
              color: statusFilter===v ? "white" : "#9CA3AF",
            }}>{l}</button>
        ))}
      </div>

      {loading ? (
        <p style={{ textAlign:"center", color:"#9CA3AF", padding:"48px 0", fontSize:"0.85rem" }}>Loading…</p>
      ) : (
        <>
          <p style={{ fontSize:"0.7rem", color:"#9CA3AF", fontWeight:500 }}>{data?.total ?? 0} complaints</p>
          <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
            {(data?.complaints ?? []).map((c) => {
              const sc = SC[c.status] ?? SC.active;
              return (
                <button key={c.complaint_id} onClick={() => onSelect(c.complaint_id)}
                  style={{ background:"white", borderRadius:14, border:"1.5px solid #E5E7EB", padding:"14px 16px", textAlign:"left", cursor:"pointer", display:"flex", alignItems:"center", gap:14, ...F, transition:"all 0.12s" }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor="#202A36"; e.currentTarget.style.boxShadow="0 2px 8px rgba(0,0,0,0.06)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor="#E5E7EB"; e.currentTarget.style.boxShadow="none"; }}>
                  {/* Dept indicator */}
                  <div style={{ width:36, height:36, borderRadius:10, background:"#F3F4F6", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"0.9rem", flexShrink:0 }}>
                    {c.department?.includes("ELECT") ? "⚡" : c.department?.includes("WATER") ? "💧" : c.department?.includes("POLICE") ? "🚔" : c.department?.includes("ROAD") ? "🛣️" : c.department?.includes("HEALTH") ? "🏥" : "📋"}
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <p style={{ fontSize:"0.85rem", fontWeight:500, color:"#111827", margin:"0 0 4px", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{c.summary || "—"}</p>
                    <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:"0.72rem", color:"#9CA3AF", flexWrap:"wrap" }}>
                      <span style={{ fontWeight:500 }}>{c.user_name}</span>
                      {c.district && <><span>·</span><span>{c.district}</span></>}
                      {c.department && <><span>·</span><span style={{ color:"#6B7280" }}>{c.department}</span></>}
                      {c.ticket_id && <span style={{ fontFamily:"monospace", color:"#3B82F6" }}>{c.ticket_id}</span>}
                    </div>
                  </div>
                  <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:5, flexShrink:0 }}>
                    <span style={{ fontSize:"0.68rem", fontWeight:700, padding:"2px 10px", borderRadius:999, background:sc.bg, color:sc.text }}>{c.status}</span>
                    <span style={{ fontSize:"0.68rem", color:"#9CA3AF" }}>{fmt(c.created_at)}</span>
                  </div>
                  <ChevronRight size={14} style={{ color:"#D1D5DB", flexShrink:0 }} />
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ── Root dashboard ────────────────────────────────────────────────────

type View =
  | { type: "stats" }
  | { type: "portals" }
  | { type: "portal"; id: string }
  | { type: "complaints" }
  | { type: "complaint"; id: string };

export function DashboardPage({ onBack, hideBackButton }: { onBack: () => void; hideBackButton?: boolean }) {
  const [view, setView] = useState<View>({ type: "stats" });
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [portals, setPortals] = useState<AdminPortal[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    adminStats().then(setStats).finally(() => setLoadingStats(false));
    adminPortals().then(setPortals);
  }, []);

  // Breadcrumb history
  const [history, setHistory] = useState<View[]>([]);

  function navigate(next: View) {
    setHistory((h) => [...h, view]);
    setView(next);
  }

  function goBack() {
    if (history.length === 0) return;
    const prev = history[history.length - 1];
    setHistory((h) => h.slice(0, -1));
    setView(prev);
  }

  const title: Record<View["type"], string> = {
    stats: "Dashboard",
    portals: "Portal Registry",
    portal: "Portal Detail",
    complaints: "All Complaints",
    complaint: "Complaint Detail",
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center gap-3 shrink-0">
        {!hideBackButton && (
          <button
            onClick={history.length > 0 ? goBack : onBack}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft size={18} className="text-gray-600" />
          </button>
        )}
        <div>
          <h1 className="font-bold text-gray-900 text-sm">{title[view.type]}</h1>
          <p className="text-xs text-gray-400">Government Dashboard</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {[["stats","Stats"],["portals","Portals"],["complaints","Complaints"]].map(([v,label]) => (
            <button
              key={v}
              onClick={() => { setHistory([]); setView({ type: v as View["type"] }); }}
              style={{ padding:"6px 16px", borderRadius:999, border:"none", fontSize:"0.78rem", fontWeight:500, cursor:"pointer", fontFamily:"'Inter',sans-serif", transition:"all 0.15s",
                background: view.type === v ? "#202A36" : "transparent",
                color: view.type === v ? "white" : "#9CA3AF",
              }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto" style={{ background:"#EEEEF0", padding:16 }}>
        {view.type === "stats" && (
          loadingStats || !stats ? (
            <p className="text-center text-gray-400 py-12">Loading…</p>
          ) : (
            <StatsView
              stats={stats}
              onPortals={() => navigate({ type: "portals" })}
              onComplaints={() => navigate({ type: "complaints" })}
            />
          )
        )}

        {view.type === "portals" && (
          <PortalListView
            portals={portals}
            onSelect={(id) => navigate({ type: "portal", id })}
          />
        )}

        {view.type === "portal" && (
          <PortalDetailView
            portalId={(view as { type: "portal"; id: string }).id}
            onComplaint={(id) => navigate({ type: "complaint", id })}
          />
        )}

        {view.type === "complaints" && (
          <ComplaintsListView onSelect={(id) => navigate({ type: "complaint", id })} />
        )}

        {view.type === "complaint" && (
          <ComplaintDetailView complaintId={(view as { type: "complaint"; id: string }).id} />
        )}
      </div>
    </div>
  );
}
