import { LogOut, Phone, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Header() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const F = { fontFamily:"'Inter',sans-serif" };

  return (
    <header style={{ background:"rgba(255,255,255,0.80)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", borderBottom:"1px solid rgba(0,0,0,0.07)", boxShadow:"0 1px 0 rgba(0,0,0,0.04), 0 2px 16px rgba(0,0,0,0.04)", flexShrink:0, position:"relative", zIndex:100 }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"10px 20px", maxWidth:"100%", ...F }}>

        {/* Brand */}
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <div>
            <div style={{ fontSize:"0.95rem", fontWeight:700, color:"#111827", letterSpacing:"-0.03em", lineHeight:1.2 }}>
              {t("appName")}
            </div>
            <div style={{ fontSize:"0.58rem", color:"#9CA3AF", fontWeight:500, letterSpacing:"0.06em", textTransform:"uppercase" }}>
              {t("tagline")}
            </div>
          </div>
        </div>

        {/* Right */}
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <div style={{ display:"flex", alignItems:"center", gap:5, padding:"4px 12px", borderRadius:999, background:"rgba(34,197,94,0.08)", border:"1px solid rgba(34,197,94,0.18)", fontSize:"0.72rem", fontWeight:500, color:"#15803D" }}>
            <span style={{ width:5, height:5, borderRadius:"50%", background:"#22c55e", display:"inline-block" }} />
            Govt. Verified
          </div>

          <LanguageSwitcher />

          <a href="tel:1234" style={{ display:"flex", alignItems:"center", gap:4, padding:"5px 14px", borderRadius:999, background:"rgba(255,255,255,0.7)", backdropFilter:"blur(8px)", border:"1px solid rgba(0,0,0,0.08)", fontSize:"0.78rem", fontWeight:500, color:"#374151", textDecoration:"none" }}>
            <Phone size={13} />
            <span>1234</span>
          </a>

          <div style={{ position:"relative" }}>
            <button onClick={() => setOpen(o => !o)}
              style={{ display:"flex", alignItems:"center", gap:7, padding:"5px 14px 5px 6px", borderRadius:999, background:"#202A36", border:"none", color:"#fff", fontSize:"0.78rem", fontWeight:500, cursor:"pointer" }}>
              <span style={{ width:24, height:24, borderRadius:"50%", background:"rgba(255,255,255,0.15)", display:"flex", alignItems:"center", justifyContent:"center" }}>
                <User size={13} />
              </span>
              <span className="hidden sm:inline">{user?.name?.split(" ")[0] || "User"}</span>
            </button>

            {open && (
              <div style={{ position:"absolute", right:0, top:"calc(100% + 8px)", background:"rgba(255,255,255,0.95)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", border:"1px solid rgba(0,0,0,0.08)", borderRadius:14, boxShadow:"0 8px 32px rgba(0,0,0,0.12)", width:220, zIndex:50, overflow:"hidden" }}>
                <div style={{ padding:"14px 16px", borderBottom:"1px solid #F3F4F6" }}>
                  <div style={{ fontSize:"0.85rem", fontWeight:600, color:"#111827" }}>{user?.name}</div>
                  <div style={{ fontSize:"0.72rem", color:"#9CA3AF", marginTop:2, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{user?.email}</div>
                </div>
                <button onClick={() => { setOpen(false); logout(); }}
                  style={{ width:"100%", display:"flex", alignItems:"center", gap:8, padding:"11px 16px", fontSize:"0.82rem", color:"#EF4444", background:"none", border:"none", cursor:"pointer", ...F }}>
                  <LogOut size={14} /> Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
