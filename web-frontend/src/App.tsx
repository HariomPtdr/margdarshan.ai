import { HelpCircle, LayoutDashboard } from "lucide-react";
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
import { attachLocation, getComplaint, getComplaintMessages, listComplaints, resetSession, restoreSession } from "./lib/api";
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
  return <MainApp />;
}

function MainApp() {
  const { t } = useTranslation();
  const [showDashboard, setShowDashboard] = useState(false);
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

  if (showDashboard) {
    return <DashboardPage onBack={() => setShowDashboard(false)} />;
  }

  return (
    <div className="h-full flex flex-col">
      <Header />
      <div className="bg-gray-50 border-b px-4 py-1 flex justify-end">
        <button
          onClick={() => setShowDashboard(true)}
          className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-blue-600 transition-colors py-1"
        >
          <LayoutDashboard size={13} /> Government Dashboard
        </button>
      </div>

      <main className="flex-1 grid grid-cols-12 overflow-hidden">
        <div className="col-span-2 hidden md:block min-w-[180px]">
          <LeftPanel
            complaints={complaints}
            activeId={chat.activeComplaintId}
            onSelect={handleSelect}
            onNew={handleNew}
          />
        </div>

        <div className="col-span-12 md:col-span-6 lg:col-span-6 overflow-hidden">
          <ChatPanel
            messages={chat.messages}
            onSend={chat.send}
            onOpenMap={() => setMapOpen(true)}
            busy={chat.busy}
            needsLocationPin={chat.needsLocationPin}
          />
        </div>

        <div className="col-span-12 md:col-span-4 lg:col-span-4 overflow-hidden">
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

