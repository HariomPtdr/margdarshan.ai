export type Intent =
  | "GREETING"
  | "SMALLTALK"
  | "COMPLAINT_NEW"
  | "COMPLAINT_CONTINUE"
  | "STATUS_CHECK"
  | "CLARIFICATION_REPLY"
  | "ABUSE"
  | "OFF_TOPIC";

export type State =
  | "IDLE"
  | "COLLECTING"
  | "READY"
  | "AWAITING_LOCATION"
  | "ASK_MORE"
  | "CONFIRMING"
  | "FIELD_COLLECTION"
  | "SUBMITTED";

export interface ChatResponse {
  reply: string;
  session_id: string;
  complaint_id?: string;
  intent: Intent;
  state: State;
  needs_location_pin: boolean;
  pipeline_triggered: boolean;
}

export interface LocationData {
  lat: number;
  lon: number;
  pincode: string;
  ward?: string;
  district: string;
  state: string;
  address_text: string;
  map_provider: string;
}

export interface PipelineEvent {
  complaint_id: string;
  stage: string;
  status: "started" | "completed" | "failed" | "skipped";
  payload: Record<string, any>;
  error?: string;
  created_at?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface ComplaintSummary {
  complaint_id: string;
  summary: string;
  status: "pending" | "active" | "resolved" | "submitted";
  created_at: number;
  department?: string;
  ticket_id?: string;
  intent?: string;
  state?: string;
  updated_at?: number;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  mobile: string;
  gender?: string | null;
  phone?: string | null;
  address?: string | null;
  sub_locality?: string | null;
  locality?: string | null;
  state?: string | null;
  district?: string | null;
  pincode?: string | null;
  country?: string | null;
}

export interface RegisterPayload {
  name: string;
  gender?: string;
  email: string;
  mobile: string;
  phone?: string;
  password: string;
  address?: string;
  sub_locality?: string;
  locality?: string;
  state?: string;
  district?: string;
  pincode?: string;
  country?: string;
}

// ── Admin / Government Dashboard ──────────────────────────────────────

export interface AdminStats {
  total_complaints: number;
  duplicate_complaints: number;
  by_status: { status: string; count: number }[];
  by_department: { department: string; count: number }[];
  by_district: { district: string; count: number }[];
  recent: { complaint_id: string; summary: string; status: string; department?: string; created_at: number }[];
}

export interface AdminPortal {
  portal_id: string;
  portal_name: string;
  portal_level: string;
  authority_name: string;
  covers_districts: string[];
  website: string;
  has_online: boolean;
  classifier_dept_tags: string[];
  complaint_categories: string;
  helpline: string;
  complaint_count: number;
}

export interface AdminComplaintRow {
  complaint_id: string;
  summary: string;
  status: string;
  department?: string;
  sub_category?: string;
  district?: string;
  portal_id?: string;
  ticket_id?: string;
  user_name: string;
  user_mobile?: string;
  priority?: string;
  sentiment?: string;
  is_duplicate?: boolean;
  duplicate_count?: number;
  created_at: number;
  updated_at?: number;
}

export interface DuplicateFiler {
  complaint_id: string;
  name: string;
  mobile: string;
  filed_at: string;
  status: string;
  similarity?: number;
  portal_fields: Record<string, string>;
}

export interface AdminComplaintDetail {
  complaint_id: string;
  summary: string;
  status: string;
  department?: string;
  sub_category?: string;
  district?: string;
  portal_id?: string;
  ticket_id?: string;
  created_at: number;
  updated_at: number;
  filer: { name: string; mobile: string; email?: string; district?: string };
  pipeline: {
    location?: any;
    nlu?: any;
    classification?: any;
    routing?: any;
    portal_fields?: Record<string, string>;
    submission?: any;
  };
  routing_explanation?: { portal_id: string; portal_name: string; level: string; reason: string };
  dedup: { is_duplicate: boolean; is_same_user: boolean; duplicate_count: number; duplicate_filers: DuplicateFiler[] };
  audit_chain: { event_id: string; event_type: string; actor: string; details: any; event_hash: string; created_at: string }[];
}
