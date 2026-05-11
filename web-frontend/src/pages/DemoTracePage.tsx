/**
 * DemoTracePage — Plug & Play live trace for presentations.
 * Shows the full API exchange: classification → routing → portal request → response → status.
 * Access: click "View API Trace" on any complaint in the department dashboard.
 */

import { ArrowRight, CheckCircle2, Code2, Globe, Send, Server, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { adminStats, getToken } from "../lib/api";

const GATEWAY = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8000";

async function fetchTrace(complaintId: string) {
  const r = await fetch(`${GATEWAY}/api/v1/demo/trace/${complaintId}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!r.ok) throw new Error("Trace not found");
  return r.json();
}

interface Props {
  complaintId: string;
  onBack: () => void;
}

export function DemoTracePage({ complaintId, onBack }: Props) {
  const [trace, setTrace] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    fetchTrace(complaintId)
      .then(setTrace)
      .catch(console.error)
      .finally(() => setLoading(false));
    // Auto-animate through steps
    const timer = setInterval(() => setActiveStep((s) => (s < 4 ? s + 1 : s)), 1500);
    return () => clearInterval(timer);
  }, [complaintId]);

  if (loading) return <div className="h-full flex items-center justify-center text-gray-500">Loading trace...</div>;
  if (!trace) return <div className="h-full flex items-center justify-center text-red-500">Trace not available</div>;

  const steps = [
    trace.step_1_classification,
    trace.step_2_routing,
    trace.step_3_api_request,
    trace.step_4_api_response,
    trace.step_5_current_status,
  ];

  const stepIcons = [<Zap size={16}/>, <Globe size={16}/>, <Send size={16}/>, <Server size={16}/>, <CheckCircle2 size={16}/>];
  const stepColors = ["bg-purple-500","bg-blue-500","bg-orange-500","bg-green-500","bg-govgreen"];

  return (
    <div className="h-full flex flex-col bg-gray-950 text-white overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Code2 size={18} className="text-saffron" />
          <span className="font-bold text-sm tracking-wider">PLUG &amp; PLAY — LIVE API TRACE</span>
          <span className="text-xs text-gray-500 font-mono">{complaintId.slice(0,8)}...</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-emerald-400 font-mono bg-emerald-400/10 px-2 py-1 rounded">
            Adapter: {trace.adapter_used}
          </span>
          <button onClick={onBack} className="text-xs text-gray-400 hover:text-white border border-gray-700 rounded px-3 py-1">← Back</button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Flow diagram */}
        <div className="flex items-center gap-1 mb-8 overflow-x-auto pb-2">
          {["Classifier", "Routing", "API Request", "Portal Response", "Status"].map((label, i) => (
            <div key={i} className="flex items-center gap-1 shrink-0">
              <div className={`flex flex-col items-center gap-1 cursor-pointer`} onClick={() => setActiveStep(i)}>
                <div className={`w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300 ${
                  i <= activeStep ? stepColors[i] : "bg-gray-700"
                }`}>
                  {stepIcons[i]}
                </div>
                <span className={`text-[10px] font-medium ${i <= activeStep ? "text-white" : "text-gray-600"}`}>{label}</span>
              </div>
              {i < 4 && <ArrowRight size={14} className={`mb-4 ${i < activeStep ? "text-gray-400" : "text-gray-700"}`} />}
            </div>
          ))}
        </div>

        {/* Active step detail */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {steps.map((step, i) => (
            <div
              key={i}
              onClick={() => setActiveStep(i)}
              className={`rounded-xl border cursor-pointer transition-all duration-300 ${
                i === activeStep
                  ? "border-saffron bg-saffron/5 shadow-lg shadow-saffron/10"
                  : i < activeStep
                  ? "border-gray-700 bg-gray-900/50"
                  : "border-gray-800 bg-gray-900/30 opacity-40"
              }`}
            >
              <div className={`flex items-center gap-2 px-4 py-2 border-b ${
                i === activeStep ? "border-saffron/30" : "border-gray-800"
              }`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white ${
                  i <= activeStep ? stepColors[i] : "bg-gray-700"
                }`}>
                  {stepIcons[i]}
                </div>
                <span className="text-xs font-bold text-gray-300">{step.label}</span>
              </div>

              <div className="p-4">
                <pre className="text-xs text-green-300 font-mono whitespace-pre-wrap leading-relaxed overflow-auto max-h-64">
                  {JSON.stringify(
                    Object.fromEntries(Object.entries(step).filter(([k]) => k !== "label")),
                    null, 2
                  )}
                </pre>
              </div>
            </div>
          ))}

          {/* Audit Chain */}
          {trace.audit_chain?.length > 0 && (
            <div className="border border-gray-800 rounded-xl bg-gray-900/50 lg:col-span-2">
              <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800">
                <CheckCircle2 size={14} className="text-yellow-400" />
                <span className="text-xs font-bold text-gray-300">AUDIT CHAIN — Tamper-Evident Event Log</span>
              </div>
              <div className="p-4 flex flex-wrap gap-2">
                {trace.audit_chain.map((e: any, i: number) => (
                  <div key={i} className="text-xs bg-gray-800 rounded-lg px-3 py-1.5">
                    <span className="text-yellow-400 font-mono">{e.at}</span>
                    <span className="text-gray-400 mx-1">→</span>
                    <span className="text-white">{e.event.replace(/_/g, " ")}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Explanation banner */}
        <div className="mt-6 bg-blue-900/30 border border-blue-700/50 rounded-xl p-4">
          <p className="text-sm text-blue-200 font-semibold mb-1">🔌 How Plug &amp; Play works here</p>
          <p className="text-xs text-blue-300/80 leading-relaxed">
            The complaint above was handled by <strong className="text-white">{trace.adapter_used}</strong>.
            To switch to a different portal, we change ONE LINE in <code className="text-saffron">registry.py</code>.
            The chatbot, routing, database, and this dashboard remain unchanged.
            Each adapter knows exactly how to talk to its portal — same interface, different implementation.
          </p>
        </div>
      </div>
    </div>
  );
}
