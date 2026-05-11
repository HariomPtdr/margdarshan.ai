import { MapPin, Mic, MicOff, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Message } from "../lib/types";
import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: Message[];
  onSend: (text: string) => void;
  onOpenMap: () => void;
  busy: boolean;
  needsLocationPin: boolean;
}

const SR_LANGS = ["hi-IN", "en-IN", "en-US"];

export function ChatPanel({ messages, onSend, onOpenMap, busy, needsLocationPin }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const [listening, setListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const langIdx = useRef(0);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  const submit = () => {
    if (!text.trim() || busy) return;
    onSend(text.trim());
    setText("");
  };

  const startVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setVoiceError("Use Chrome browser for voice."); setTimeout(() => setVoiceError(""), 3000); return; }
    setVoiceError("");
    const lang = SR_LANGS[langIdx.current % SR_LANGS.length];
    const rec = new SR();
    rec.lang = lang; rec.interimResults = true; rec.continuous = true; rec.maxAlternatives = 1;
    rec.onstart = () => setListening(true);
    rec.onresult = (e: any) => {
      let transcript = "";
      for (let i = 0; i < e.results.length; i++) transcript += e.results[i][0].transcript;
      setText(transcript.trim());
    };
    rec.onerror = (e: any) => {
      if (e.error === "not-allowed") setVoiceError("Microphone blocked. Allow mic in browser.");
      else if (e.error !== "aborted" && e.error !== "no-speech") setVoiceError(`Mic error: ${e.error}`);
      setTimeout(() => setVoiceError(""), 3000);
      setListening(false);
    };
    rec.onend = () => setListening(false);
    try { rec.start(); recognitionRef.current = rec; }
    catch { setVoiceError("Could not start mic."); setTimeout(() => setVoiceError(""), 3000); }
  };

  const stopVoice = () => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
    setTimeout(() => {
      setText((current) => {
        const trimmed = current.trim();
        if (trimmed && !busy) { onSend(trimmed); return ""; }
        return current;
      });
    }, 300);
  };

  return (
    <section className="h-full flex flex-col" style={{ background:"rgba(255,255,255,0.60)", backdropFilter:"blur(20px)", WebkitBackdropFilter:"blur(20px)", fontFamily:"'Inter',sans-serif" }}>

      {messages.length === 0 && (
        <div className="px-6 py-16 text-center max-w-sm mx-auto">
          <div style={{ width:52, height:52, borderRadius:16, background:"rgba(255,255,255,0.9)", border:"1px solid rgba(0,0,0,0.08)", backdropFilter:"blur(12px)", display:"flex", alignItems:"center", justifyContent:"center", margin:"0 auto 16px", boxShadow:"0 4px 16px rgba(0,0,0,0.08)", fontSize:"1rem", fontWeight:700, color:"#202A36", letterSpacing:"-0.02em" }}>M</div>
          <h3 style={{ color:"#111827", fontWeight:600, fontSize:"1.05rem", fontFamily:"'Inter',sans-serif", marginBottom:6, letterSpacing:"-0.02em" }}>{t("chat.welcomeTitle")}</h3>
          <p style={{ color:"#6B7280", lineHeight:1.7, fontSize:"0.82rem" }}>{t("chat.welcomeBody")}</p>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 md:px-6 py-4 space-y-3" style={{ background:"transparent" }}>
        {messages.map((m, idx) => {
          const isLastBot = m.role === "assistant" && idx === messages.map((x) => x.role).lastIndexOf("assistant");
          return (
            <MessageBubble
              key={m.id}
              message={m}
              onChipSelect={isLastBot && !busy ? (v) => { onSend(v); } : undefined}
            />
          );
        })}
        {busy && (
          <div className="flex justify-start">
            <div className="bubble-bot px-4 py-2.5">
              <span className="step-pulse" style={{ color:"#9CA3AF" }}>•••</span>
            </div>
          </div>
        )}
      </div>

      {needsLocationPin && (
        <div style={{ padding:"0 12px 8px" }}>
          <button onClick={onOpenMap}
            style={{ width:"100%", padding:"10px", borderRadius:999, background:"#202A36", border:"none", color:"#fff", fontSize:"0.82rem", fontWeight:600, display:"flex", alignItems:"center", justifyContent:"center", gap:7, cursor:"pointer", fontFamily:"'Inter',sans-serif", boxShadow:"0 2px 12px rgba(32,42,54,0.3)" }}>
            <MapPin size={16} />
            {t("chat.openMap")}
          </button>
        </div>
      )}

      {voiceError && (
        <div style={{ margin:"0 12px 8px", fontSize:"0.75rem", color:"#DC2626", background:"rgba(254,242,242,0.9)", border:"1px solid rgba(220,38,38,0.15)", padding:"8px 14px", borderRadius:10 }}>
          {voiceError}
        </div>
      )}

      {/* Input bar */}
      <div style={{ padding:"10px 14px 12px", background:"rgba(255,255,255,0.7)", backdropFilter:"blur(16px)", WebkitBackdropFilter:"blur(16px)", borderTop:"1px solid rgba(0,0,0,0.06)" }}>
        <div style={{ display:"flex", alignItems:"flex-end", gap:8, background:"rgba(255,255,255,0.85)", backdropFilter:"blur(12px)", WebkitBackdropFilter:"blur(12px)", borderRadius:999, padding:"6px 6px 6px 14px", border:"1px solid rgba(0,0,0,0.08)", boxShadow:"0 2px 12px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.9)" }}>
          <button
            onMouseDown={startVoice} onMouseUp={stopVoice} onMouseLeave={stopVoice}
            onTouchStart={(e) => { e.preventDefault(); startVoice(); }}
            onTouchEnd={(e) => { e.preventDefault(); stopVoice(); }}
            className="shrink-0 select-none"
            style={{ width:32, height:32, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", background: listening ? "#EF4444" : "transparent", color: listening ? "#fff" : "#9CA3AF", border:"none", flexShrink:0, transition:"all 0.15s" }}>
            {listening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
            placeholder={listening ? "🎤 Listening..." : t("chat.placeholder")}
            rows={1}
            style={{ flex:1, resize:"none", background:"transparent", border:"none", outline:"none", fontFamily:"'Inter',sans-serif", fontSize:"0.85rem", color:"#111827", lineHeight:1.5, maxHeight:96, padding:"4px 0" }}
          />

          <button onClick={submit} disabled={!text.trim() || busy}
            style={{ width:36, height:36, borderRadius:"50%", background: text.trim() && !busy ? "#202A36" : "#E5E7EB", border:"none", color: text.trim() && !busy ? "#fff" : "#9CA3AF", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0, transition:"all 0.15s", cursor: text.trim() && !busy ? "pointer" : "default", boxShadow: text.trim() && !busy ? "0 2px 8px rgba(32,42,54,0.25)" : "none" }}>
            <Send size={15} />
          </button>
        </div>
        {listening && (
          <p style={{ fontSize:"0.72rem", textAlign:"center", color:"#EF4444", marginTop:6, fontWeight:500 }}>
            🔴 Recording... release button to stop
          </p>
        )}
      </div>
    </section>
  );
}
