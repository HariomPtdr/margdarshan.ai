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
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  adminComplaintDetail,
  adminComplaints,
  adminPortalDetail,
  adminPortals,
  adminStats,
} from "../lib/api";
import type {
  AdminComplaintDetail,
  AdminComplaintRow,
  AdminPortal,
  AdminStats,
} from "../lib/types";

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

function StatsView({
  stats,
  onPortals,
  onComplaints,
}: {
  stats: AdminStats;
  onPortals: () => void;
  onComplaints: () => void;
}) {
  const statusMap = Object.fromEntries(stats.by_status.map((s) => [s.status, s.count]));

  return (
    <div className="space-y-6">
      {/* Top metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Complaints", value: stats.total_complaints, icon: FileText, color: "text-blue-600" },
          { label: "Submitted", value: statusMap["submitted"] ?? 0, icon: CheckCircle, color: "text-yellow-600" },
          { label: "Resolved", value: statusMap["resolved"] ?? 0, icon: Shield, color: "text-green-600" },
          { label: "Duplicates Found", value: stats.duplicate_complaints, icon: Copy, color: "text-orange-600" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border p-4 flex items-center gap-3">
            <Icon size={24} className={color} />
            <div>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top departments */}
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <BarChart2 size={16} /> Top Departments
          </h3>
          {stats.by_department.slice(0, 6).map(({ department, count }) => (
            <div key={department} className="flex items-center gap-2 mb-2">
              <span className="text-sm text-gray-700 w-40 truncate">{department}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div
                  className="bg-orange-400 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (count / (stats.total_complaints || 1)) * 100)}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-6 text-right">{count}</span>
            </div>
          ))}
        </div>

        {/* Top districts */}
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <MapPin size={16} /> Top Districts
          </h3>
          {stats.by_district.slice(0, 6).map(({ district, count }) => (
            <div key={district} className="flex items-center gap-2 mb-2">
              <span className="text-sm text-gray-700 w-40 truncate">{district}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div
                  className="bg-blue-400 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (count / (stats.total_complaints || 1)) * 100)}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-6 text-right">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent complaints */}
      <div className="bg-white rounded-xl border p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <Clock size={16} /> Recent Complaints
          </h3>
          <button onClick={onComplaints} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
            View all <ChevronRight size={12} />
          </button>
        </div>
        <div className="divide-y">
          {stats.recent.map((c) => (
            <div key={c.complaint_id} className="py-2 flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-800 truncate">{c.summary}</p>
                <p className="text-xs text-gray-400">{c.department} · {fmt(c.created_at)}</p>
              </div>
              <Badge label={c.status} color={statusColor(c.status)} />
            </div>
          ))}
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={onPortals}
          className="bg-white rounded-xl border p-4 flex items-center gap-3 hover:border-blue-400 transition-colors text-left"
        >
          <Globe size={20} className="text-blue-500" />
          <div>
            <p className="font-semibold text-gray-800">Portal Registry</p>
            <p className="text-xs text-gray-500">Browse all 70 portals</p>
          </div>
          <ChevronRight size={16} className="ml-auto text-gray-400" />
        </button>
        <button
          onClick={onComplaints}
          className="bg-white rounded-xl border p-4 flex items-center gap-3 hover:border-blue-400 transition-colors text-left"
        >
          <FileText size={20} className="text-orange-500" />
          <div>
            <p className="font-semibold text-gray-800">All Complaints</p>
            <p className="text-xs text-gray-500">{stats.total_complaints} total</p>
          </div>
          <ChevronRight size={16} className="ml-auto text-gray-400" />
        </button>
      </div>
    </div>
  );
}

// ── Portal list ───────────────────────────────────────────────────────

function PortalListView({
  portals,
  onSelect,
}: {
  portals: AdminPortal[];
  onSelect: (id: string) => void;
}) {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState<string>("All");

  const filtered = portals.filter((p) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q || p.portal_name.toLowerCase().includes(q) || p.authority_name.toLowerCase().includes(q);
    const matchLevel = levelFilter === "All" || p.portal_level === levelFilter;
    return matchSearch && matchLevel;
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <input
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          placeholder="Search portals…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {["All", "Regional", "State", "Central"].map((l) => (
          <button
            key={l}
            onClick={() => setLevelFilter(l)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              levelFilter === l ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      <p className="text-xs text-gray-500">{filtered.length} portals</p>

      <div className="space-y-2">
        {filtered.map((p) => (
          <button
            key={p.portal_id}
            onClick={() => onSelect(p.portal_id)}
            className="w-full bg-white rounded-xl border p-4 hover:border-blue-400 transition-colors text-left flex items-start gap-3"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="font-medium text-gray-900 text-sm">{p.portal_name}</span>
                <Badge label={p.portal_level} color={levelBadge(p.portal_level)} />
                {p.has_online && <Badge label="Online" color="bg-green-100 text-green-700" />}
              </div>
              <p className="text-xs text-gray-500 truncate">{p.authority_name}</p>
              {p.helpline && (
                <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                  <Phone size={10} /> {p.helpline}
                </p>
              )}
            </div>
            <div className="text-right shrink-0">
              <p className="text-xl font-bold text-blue-600">{p.complaint_count}</p>
              <p className="text-xs text-gray-400">complaints</p>
            </div>
            <ChevronRight size={16} className="text-gray-300 self-center" />
          </button>
        ))}
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

  return (
    <div className="space-y-5">
      {/* Portal info card */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h2 className="text-lg font-bold text-gray-900">{portal.portal_name}</h2>
              <Badge label={portal.portal_level} color={levelBadge(portal.portal_level)} />
            </div>
            <p className="text-sm text-gray-600">{portal.authority_name}</p>
          </div>
          <a
            href={portal.website}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-xs text-blue-600 hover:underline shrink-0"
          >
            <ExternalLink size={12} /> Portal
          </a>
        </div>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          {portal.helpline && (
            <div className="flex items-center gap-2 text-gray-600">
              <Phone size={14} /> {portal.helpline}
            </div>
          )}
          <div className="flex items-center gap-2 text-gray-600">
            <Activity size={14} /> {portal.complaint_count} complaints
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Globe size={14} /> {portal.has_online ? "Online submission" : "Offline only"}
          </div>
        </div>

        {portal.classifier_dept_tags?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {portal.classifier_dept_tags.slice(0, 8).map((t) => (
              <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{t}</span>
            ))}
            {portal.classifier_dept_tags.length > 8 && (
              <span className="text-xs text-gray-400">+{portal.classifier_dept_tags.length - 8} more</span>
            )}
          </div>
        )}
      </div>

      {/* Complaints */}
      <div className="bg-white rounded-xl border p-4">
        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <FileText size={16} /> Complaints ({data.total})
        </h3>
        {complaints.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">No complaints routed to this portal yet.</p>
        ) : (
          <div className="divide-y">
            {complaints.map((c) => (
              <button
                key={c.complaint_id}
                onClick={() => onComplaint(c.complaint_id)}
                className="w-full text-left py-3 flex items-start gap-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 truncate">{c.summary}</p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="text-xs text-gray-400">{c.user_name}</span>
                    {c.district && <span className="text-xs text-gray-400">· {c.district}</span>}
                    {c.department && <span className="text-xs text-gray-400">· {c.department}</span>}
                    {c.is_duplicate && (
                      <span className="text-xs text-orange-600 flex items-center gap-0.5">
                        <Users size={10} /> {c.duplicate_count} duplicate(s)
                      </span>
                    )}
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <Badge label={c.status} color={statusColor(c.status)} />
                  <span className="text-xs text-gray-400">{fmt(c.created_at)}</span>
                </div>
                <ChevronRight size={14} className="text-gray-300 self-center" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Complaint detail ──────────────────────────────────────────────────

function ComplaintDetailView({ complaintId }: { complaintId: string }) {
  const [detail, setDetail] = useState<AdminComplaintDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAudit, setShowAudit] = useState(false);

  useEffect(() => {
    adminComplaintDetail(complaintId).then(setDetail).finally(() => setLoading(false));
  }, [complaintId]);

  if (loading) return <p className="text-center text-gray-400 py-12">Loading…</p>;
  if (!detail) return <p className="text-center text-red-400 py-12">Complaint not found.</p>;

  const cls = detail.pipeline.classification;
  const loc = detail.pipeline.location;
  const pf  = detail.pipeline.portal_fields;
  const sub = detail.pipeline.submission;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs text-gray-400 mb-1 font-mono">{detail.complaint_id}</p>
            <p className="text-base font-semibold text-gray-900">{detail.summary}</p>
          </div>
          <Badge label={detail.status} color={statusColor(detail.status)} />
        </div>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><p className="text-xs text-gray-400">Filed by</p><p className="font-medium">{detail.filer.name}</p></div>
          <div><p className="text-xs text-gray-400">Mobile</p><p className="font-medium">{detail.filer.mobile}</p></div>
          <div><p className="text-xs text-gray-400">District</p><p className="font-medium">{detail.district || "—"}</p></div>
          <div><p className="text-xs text-gray-400">Filed</p><p className="font-medium">{fmt(detail.created_at)}</p></div>
        </div>

        {detail.ticket_id && (
          <div className="mt-3 p-3 bg-green-50 rounded-lg flex items-center gap-2">
            <Hash size={14} className="text-green-600" />
            <span className="text-sm font-mono text-green-800">{detail.ticket_id}</span>
            <span className="text-xs text-green-600 ml-2">Portal ticket</span>
          </div>
        )}
      </div>

      {/* Classification */}
      {cls && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2"><BarChart2 size={15} /> Classification</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {[
              ["Department", cls.department],
              ["Sub-category", cls.sub_category],
              ["Priority", cls.priority],
              ["Sentiment", cls.sentiment],
            ].map(([k, v]) => (
              <div key={k}><p className="text-xs text-gray-400">{k}</p><p className="font-medium">{v || "—"}</p></div>
            ))}
          </div>
          {cls.confidence !== undefined && (
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs text-gray-400">Confidence</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${Math.round(cls.confidence * 100)}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">{Math.round(cls.confidence * 100)}%</span>
            </div>
          )}
        </div>
      )}

      {/* Routing explanation */}
      {detail.routing_explanation && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2"><Globe size={15} /> Routing Decision</h3>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="font-medium text-gray-900">{detail.routing_explanation.portal_name}</span>
            <Badge label={detail.routing_explanation.level} color={levelBadge(detail.routing_explanation.level)} />
          </div>
          <p className="text-sm text-gray-600">{detail.routing_explanation.reason}</p>
        </div>
      )}

      {/* Portal fields collected */}
      {pf && Object.keys(pf).length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2"><Building2 size={15} /> Collected Portal Fields</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {Object.entries(pf).map(([k, v]) => (
              <div key={k} className="bg-gray-50 rounded-lg p-2">
                <p className="text-xs text-gray-400">{k}</p>
                <p className="text-sm font-medium text-gray-800 break-all">{v as string}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Duplicate filers */}
      {detail.dedup.is_duplicate && !detail.dedup.is_same_user && detail.dedup.duplicate_count > 0 && (
        <div className="bg-orange-50 rounded-xl border border-orange-200 p-4">
          <h3 className="font-semibold text-orange-800 mb-3 flex items-center gap-2">
            <Users size={15} /> {detail.dedup.duplicate_count} Other Person(s) Filed the Same Complaint
          </h3>
          <div className="space-y-3">
            {detail.dedup.duplicate_filers.map((f) => (
              <div key={f.complaint_id} className="bg-white rounded-lg border border-orange-100 p-3">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-medium text-gray-800">{f.name}</span>
                    <span className="text-xs text-gray-500 ml-2">{f.mobile}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {f.similarity !== undefined && f.similarity > 0 && (
                      <span className="text-xs text-orange-600">{Math.round(f.similarity * 100)}% match</span>
                    )}
                    <Badge label={f.status} color={statusColor(f.status)} />
                  </div>
                </div>
                <p className="text-xs text-gray-400">{new Date(f.filed_at).toLocaleString("en-IN")}</p>
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

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        {["", "active", "submitted", "in_progress", "resolved", "rejected"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              statusFilter === s ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-center text-gray-400 py-12">Loading…</p>
      ) : (
        <>
          <p className="text-xs text-gray-500">{data?.total ?? 0} complaints</p>
          <div className="space-y-2">
            {(data?.complaints ?? []).map((c) => (
              <button
                key={c.complaint_id}
                onClick={() => onSelect(c.complaint_id)}
                className="w-full bg-white rounded-xl border p-4 text-left hover:border-blue-400 transition-colors flex items-start gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 truncate">{c.summary}</p>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-400 flex-wrap">
                    <span>{c.user_name}</span>
                    {c.district && <span>· {c.district}</span>}
                    {c.department && <span>· {c.department}</span>}
                    {c.ticket_id && <span className="font-mono text-green-600">· {c.ticket_id}</span>}
                    {c.is_duplicate && (
                      <span className="text-orange-500 flex items-center gap-0.5">
                        <AlertCircle size={10} /> {c.duplicate_count} dup
                      </span>
                    )}
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <Badge label={c.status} color={statusColor(c.status)} />
                  <span className="text-xs text-gray-400">{fmt(c.created_at)}</span>
                </div>
                <ChevronRight size={14} className="text-gray-300 self-center" />
              </button>
            ))}
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

export function DashboardPage({ onBack }: { onBack: () => void }) {
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
        <button
          onClick={history.length > 0 ? goBack : onBack}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft size={18} className="text-gray-600" />
        </button>
        <div>
          <h1 className="font-bold text-gray-900 text-sm">{title[view.type]}</h1>
          <p className="text-xs text-gray-400">Government Dashboard</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {["stats", "portals", "complaints"].map((v) => (
            <button
              key={v}
              onClick={() => { setHistory([]); setView({ type: v as View["type"] }); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                view.type === v ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
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
