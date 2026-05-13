import { HelpCircle, LogOut } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { v4 as uuid } from "uuid";

import { ChatPanel } from "./components/ChatPanel";
import { Header } from "./components/Header";
import { LeftPanel } from "./components/LeftPanel";
import { MapModal } from "./components/MapModal";
import { RightPanel } from "./components/RightPanel";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { useChat } from "./hooks/useChat";
import { usePipeline, type PipelineState } from "./hooks/usePipeline";
import { adminStats, attachLocation, getComplaint, getComplaintMessages, listComplaints, resetSession, restoreSession } from "./lib/api";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import type { ComplaintSummary, Message } from "./lib/types";

export default function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  );
}

function Root() {
  const { user, loading } = useAuth();
  const [authView, setAuthView] = useState<"login" | "signup">("login");
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

  // After login, check if this account has admin access
  useEffect(() => {
    if (!user) { setIsAdmin(null); return; }
    adminStats()
      .then(() => setIsAdmin(true))
      .catch(() => setIsAdmin(false));
  }, [user]);

  if (loading) {
    return <div className="h-full flex items-center justify-center text-gray-500">Loading...</div>;
  }

  if (!user) {
    return authView === "login" ? (
      <LoginPage onSwitchToSignup={() => setAuthView("signup")} />
    ) : (
      <SignupPage onSwitchToLogin={() => setAuthView("login")} />
    );
  }

  // Still checking admin role
  if (isAdmin === null) {
    return <div className="h-full flex items-center justify-center text-gray-500">Loading...</div>;
  }

  // Admin → department dashboard, citizen → main app
  if (isAdmin) {
    return <AdminDashboard />;
  }

  return <MainApp />;
}

function AdminDashboard() {
  const { logout } = useAuth();
  return (
    <div className="h-full flex flex-col" style={{ background:"linear-gradient(135deg, #EDF2F7 0%, #F0F4F9 50%, #EBF0F7 100%)" }}>
      <div style={{ background:"#202A36", borderBottom:"1px solid rgba(0,0,0,0.1)", color:"white", padding:"10px 20px", display:"flex", alignItems:"center", justifyContent:"space-between", flexShrink:0, fontFamily:"'Inter',sans-serif" }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div>
            <p style={{ margin:0, fontSize:"0.85rem", fontWeight:600, letterSpacing:"-0.01em" }}>Margdarshan.ai</p>
            <p style={{ margin:0, fontSize:"0.62rem", color:"rgba(255,255,255,0.45)", fontWeight:500, letterSpacing:"0.03em" }}>DEPARTMENT DASHBOARD</p>
          </div>
        </div>
        <button onClick={logout}
          style={{ display:"flex", alignItems:"center", gap:6, padding:"6px 14px", borderRadius:999, background:"rgba(255,255,255,0.1)", border:"1px solid rgba(255,255,255,0.15)", color:"rgba(255,255,255,0.8)", fontSize:"0.75rem", fontWeight:500, cursor:"pointer", fontFamily:"'Inter',sans-serif" }}>
          <LogOut size={13} /> Sign out
        </button>
      </div>
      <div className="flex-1 overflow-hidden">
        <DashboardPage onBack={() => {}} hideBackButton />
      </div>
    </div>
  );
}

function MainApp() {
  const { t } = useTranslation();
  const chat = useChat();
  const [seedByComplaint, setSeedByComplaint] = useState<Record<string, PipelineState>>({});
  const seed = chat.activeComplaintId ? seedByComplaint[chat.activeComplaintId] : undefined;
  const pipeline = usePipeline(chat.activeComplaintId, seed);
  const [mapOpen, setMapOpen] = useState(false);
  const [complaints, setComplaints] = useState<ComplaintSummary[]>([]);

  const refreshComplaints = useCallback(async () => {
    try {
      const list = await listComplaints();
      setComplaints(list);
    } catch (e) {
      console.error("Failed to load complaints", e);
    }
  }, []);

  useEffect(() => {
    refreshComplaints();
  }, [refreshComplaints]);

  useEffect(() => {
    if (chat.activeComplaintId) refreshComplaints();
  }, [chat.activeComplaintId, refreshComplaints]);

  useEffect(() => {
    if (pipeline.classification || pipeline.routing || pipeline.submission) {
      const t = setTimeout(refreshComplaints, 400);
      return () => clearTimeout(t);
    }
  }, [pipeline.classification, pipeline.routing, pipeline.submission, refreshComplaints]);

  // When classifier confidence is low, inject the clarifying question as a bot message.
  useEffect(() => {
    if (pipeline.clarifyingQuestion) {
      chat.setMessages((prev: any) => {
        if (prev.some((m: any) => m.content === pipeline.clarifyingQuestion)) return prev;
        return [
          ...prev,
          {
            id: uuid(),
            role: "assistant" as const,
            content: pipeline.clarifyingQuestion!,
            timestamp: Date.now(),
          },
        ];
      });
    }
  }, [pipeline.clarifyingQuestion]);

  // When the pipeline proactively pushes a field-collection opening message,
  // inject it into the chat panel immediately without waiting for a user turn.
  useEffect(() => {
    if (!pipeline.fieldCollectionMessage) return;
    chat.setMessages((prev: any) => {
      if (prev.some((m: any) => m.content === pipeline.fieldCollectionMessage)) return prev;
      return [
        ...prev,
        {
          id: uuid(),
          role: "assistant" as const,
          content: pipeline.fieldCollectionMessage!,
          timestamp: Date.now(),
        },
      ];
    });
  }, [pipeline.fieldCollectionMessage]);

  // Status change notification from tracker — show in chat.
  useEffect(() => {
    if (!pipeline.trackerStatus?.canonical_status) return;
    const s = pipeline.trackerStatus;
    const msg = `Status update: your complaint is now ${s.canonical_status}. Portal: ${s.portal_status_raw || ""}`;
    chat.setMessages((prev: any) => {
      if (prev.some((m: any) => m.content === msg)) return prev;
      return [...prev, { id: uuid(), role: "assistant" as const, content: msg, timestamp: Date.now() }];
    });
  }, [pipeline.trackerStatus]);

  const handleConfirmLocation = async (lat: number, lon: number) => {
    if (!chat.activeComplaintId) {
      console.warn("No active complaint ID when confirming location");
      return;
    }
    try {
      await attachLocation(chat.activeComplaintId, lat, lon);
      chat.setNeedsLocationPin(false);
      // Add a bot message so user knows location was received
      chat.setMessages((prev: any) => [
        ...prev,
        {
          id: Math.random().toString(),
          role: "assistant" as const,
          content: "📍 Location received! Processing your complaint now...",
          timestamp: Date.now(),
        },
      ]);
      setTimeout(refreshComplaints, 1500);
    } catch (e) {
      console.error("attach-location failed:", e);
    }
  };

  const handleNew = () => {
    resetSession().catch(() => {});
    chat.reset();
  };

  const handleSelect = useCallback(
    async (id: string) => {
      if (id === chat.activeComplaintId) return;
      try {
        const [detail, msgs] = await Promise.all([
          getComplaint(id),
          getComplaintMessages(id),
        ]);
        const pd = detail.pipeline_data || {};

        // Build pipeline seed from stored data.
        const stages: PipelineState["stages"] = {};
        if (pd.location) stages["stage_1_intake"] = "completed";
        if (pd.nlu) stages["stage_2_nlu"] = "completed";
        if (pd.classification) stages["stage_3_classify"] = "completed";
        if (pd.routing) stages["stage_5_route"] = "completed";
        if (pd.submission) stages["stage_8_submit"] = "completed";

        const seedState: PipelineState = {
          stages,
          location: pd.location,
          nluPayload: pd.nlu,
          classification: pd.classification,
          routing: pd.routing,
          submission: pd.submission,
        };
        setSeedByComplaint((prev) => ({ ...prev, [id]: seedState }));

        const replay: Message[] = msgs.length
          ? msgs.map((m) => ({
              id: uuid(),
              role: m.role,
              content: m.content,
              timestamp: m.timestamp,
            }))
          : [
              {
                id: uuid(),
                role: "user",
                content: detail.summary || "(complaint)",
                timestamp: detail.created_at,
              },
            ];

        // Restore session only for truly in-progress complaints (no routing yet).
        // For routed/submitted complaints, just view — don't continue in this session.
        const hasRouting = !!(pd.routing && Object.keys(pd.routing).length > 0);
        const isComplete = detail.status === "submitted" || detail.status === "resolved" || hasRouting;
        if (isComplete) {
          resetSession().catch(() => {});
        } else {
          restoreSession(id).catch(() => {});
        }
        chat.setMessages(replay);
        chat.setSessionId(undefined);
        chat.setNeedsLocationPin(false);
        chat.setActiveComplaintId(id);
      } catch (e) {
        console.error("Failed to load complaint", e);
      }
    },
    [chat],
  );

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background:"linear-gradient(135deg, #EDF2F7 0%, #F0F4F9 50%, #EBF0F7 100%)" }}>
      <Header />
      {/* min-h-0 lets the grid shrink below the natural height of its tallest child
          (the LeftPanel complaint list). Without it, that list expands the grid row
          and pushes the ChatPanel's input bar past the viewport with no way to scroll. */}
      <main className="flex-1 grid grid-cols-12 overflow-hidden min-h-0" style={{ gap:0 }}>
        {/* Left panel */}
        <div className="col-span-2 hidden md:block min-w-[180px] min-h-0 overflow-hidden">
          <LeftPanel
            complaints={complaints}
            activeId={chat.activeComplaintId}
            onSelect={handleSelect}
            onNew={handleNew}
          />
        </div>

        {/* Chat */}
        <div className="col-span-12 md:col-span-6 lg:col-span-6 overflow-hidden min-h-0" style={{ borderRight:"1px solid rgba(255,255,255,0.07)" }}>
          <ChatPanel
            messages={chat.messages}
            onSend={chat.send}
            onOpenMap={() => setMapOpen(true)}
            busy={chat.busy}
            needsLocationPin={chat.needsLocationPin}
          />
        </div>

        {/* Right panel */}
        <div className="col-span-12 md:col-span-4 lg:col-span-4 overflow-hidden min-h-0">
          <RightPanel state={pipeline} hasActiveComplaint={!!chat.activeComplaintId} />
        </div>
      </main>

      <button
        className="fixed bottom-4 right-4 md:hidden bg-saffron text-white rounded-full px-4 py-3 shadow-lg flex items-center gap-2 font-semibold"
        title={t("help")}
      >
        <HelpCircle size={20} />
      </button>

      <MapModal
        open={mapOpen}
        onClose={() => setMapOpen(false)}
        onConfirm={handleConfirmLocation}
      />
    </div>
  );
}

