import type {
  AdminComplaintDetail,
  AdminComplaintRow,
  AdminPortal,
  AdminStats,
  AuthUser,
  ChatResponse,
  ComplaintSummary,
  LocationData,
  RegisterPayload,
} from "./types";

const GATEWAY = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8000";

const TOKEN_KEY = "shikayat_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function handle<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let detail = `HTTP ${r.status}`;
    try {
      const j = await r.json();
      detail = j.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return r.json() as Promise<T>;
}

// ── Auth ────────────────────────────────────────────────────────────────

export async function register(payload: RegisterPayload): Promise<{ token: string; user: AuthUser }> {
  const r = await fetch(`${GATEWAY}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(r);
}

export async function login(identifier: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const r = await fetch(`${GATEWAY}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier, password }),
  });
  return handle(r);
}

export async function fetchMe(): Promise<AuthUser> {
  const r = await fetch(`${GATEWAY}/api/v1/auth/me`, { headers: authHeaders() });
  return handle(r);
}

// ── Chat ────────────────────────────────────────────────────────────────

export async function sendChat(
  message: string,
  session_id: string | undefined,
  language_preference: string,
): Promise<ChatResponse> {
  const r = await fetch(`${GATEWAY}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id, message, language_preference }),
  });
  return handle(r);
}

export async function attachLocation(
  complaint_id: string,
  lat: number,
  lon: number,
): Promise<{ status: string; location: LocationData }> {
  const r = await fetch(`${GATEWAY}/api/v1/complaint/attach-location`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ complaint_id, lat, lon }),
  });
  return handle(r);
}

// ── Session ─────────────────────────────────────────────────────────────

export async function resetSession(): Promise<void> {
  await fetch(`${GATEWAY}/api/v1/session/reset`, {
    method: "POST",
    headers: authHeaders(),
  });
}

export async function restoreSession(complaint_id: string): Promise<void> {
  await fetch(`${GATEWAY}/api/v1/session/restore/${complaint_id}`, {
    method: "POST",
    headers: authHeaders(),
  });
}

// ── Complaints ──────────────────────────────────────────────────────────

export async function listComplaints(): Promise<ComplaintSummary[]> {
  const r = await fetch(`${GATEWAY}/api/v1/complaints`, { headers: authHeaders() });
  return handle(r);
}

export async function getComplaint(id: string): Promise<any> {
  const r = await fetch(`${GATEWAY}/api/v1/complaints/${id}`, { headers: authHeaders() });
  return handle(r);
}

export async function getComplaintMessages(
  id: string,
): Promise<Array<{ role: "user" | "assistant"; content: string; timestamp: number }>> {
  const r = await fetch(`${GATEWAY}/api/v1/complaints/${id}/messages`, { headers: authHeaders() });
  return handle(r);
}

// ── Admin / Government Dashboard ────────────────────────────────────────

export async function adminStats(): Promise<AdminStats> {
  const r = await fetch(`${GATEWAY}/api/v1/admin/stats`, { headers: authHeaders() });
  return handle(r);
}

export async function adminPortals(): Promise<AdminPortal[]> {
  const r = await fetch(`${GATEWAY}/api/v1/admin/portals`, { headers: authHeaders() });
  return handle(r);
}

export async function adminPortalDetail(
  portalId: string,
): Promise<{ portal: AdminPortal; complaints: AdminComplaintRow[]; total: number }> {
  const r = await fetch(`${GATEWAY}/api/v1/admin/portals/${portalId}`, { headers: authHeaders() });
  return handle(r);
}

export async function adminComplaints(params?: {
  status?: string; department?: string; district?: string; limit?: number; offset?: number;
}): Promise<{ complaints: AdminComplaintRow[]; total: number }> {
  const q = new URLSearchParams();
  if (params?.status)     q.set("status", params.status);
  if (params?.department) q.set("department", params.department);
  if (params?.district)   q.set("district", params.district);
  if (params?.limit)      q.set("limit", String(params.limit));
  if (params?.offset)     q.set("offset", String(params.offset));
  const r = await fetch(`${GATEWAY}/api/v1/admin/complaints?${q}`, { headers: authHeaders() });
  return handle(r);
}

export async function adminComplaintDetail(id: string): Promise<AdminComplaintDetail> {
  const r = await fetch(`${GATEWAY}/api/v1/admin/complaints/${id}`, { headers: authHeaders() });
  return handle(r);
}

// ── WebSocket ───────────────────────────────────────────────────────────

export function pipelineWebSocket(complaint_id: string): WebSocket {
  const url = GATEWAY.replace(/^http/, "ws");
  return new WebSocket(`${url}/ws/pipeline/${complaint_id}`);
}
