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

// Languages to try for speech recognition — rotates on each tap.
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
    if (!SR) {
      setVoiceError("Use Chrome browser for voice.");
      setTimeout(() => setVoiceError(""), 3000);
      return;
    }
    setVoiceError("");
    const lang = SR_LANGS[langIdx.current % SR_LANGS.length];
    const rec = new SR();
    rec.lang = lang;
    rec.interimResults = true;
    rec.continuous = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => setListening(true);

    rec.onresult = (e: any) => {
      let transcript = "";
      for (let i = 0; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript;
      }
      setText(transcript.trim());
    };

    rec.onerror = (e: any) => {
      if (e.error === "not-allowed") {
        setVoiceError("Microphone blocked. Allow mic in browser.");
      } else if (e.error !== "aborted" && e.error !== "no-speech") {
        setVoiceError(`Mic error: ${e.error}`);
      }
      setTimeout(() => setVoiceError(""), 3000);
      setListening(false);
    };

    rec.onend = () => setListening(false);

    try {
      rec.start();
      recognitionRef.current = rec;
    } catch {
      setVoiceError("Could not start mic.");
      setTimeout(() => setVoiceError(""), 3000);
    }
  };

  const stopVoice = () => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
    // Auto-send transcribed text after releasing mic
    setTimeout(() => {
      setText((current) => {
        const trimmed = current.trim();
        if (trimmed && !busy) {
          onSend(trimmed);
          return "";
        }
        return current;
      });
    }, 300); // small delay to let final transcript arrive
  };

  return (
    <section className="h-full flex flex-col bg-gray-50">
      {messages.length === 0 && (
        <div className="px-6 py-12 text-center max-w-md mx-auto">
          <div className="text-6xl mb-3">🙏</div>
          <h3 className="text-xl font-bold text-gray-900 mb-1">{t("chat.welcomeTitle")}</h3>
          <p className="text-sm text-gray-600">{t("chat.welcomeBody")}</p>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 md:px-6 py-4 space-y-3">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {busy && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-500 px-4 py-2.5 rounded-2xl rounded-bl-sm border border-gray-200 shadow-sm">
              <span className="step-pulse">...</span>
            </div>
          </div>
        )}
      </div>

      {needsLocationPin && (
        <div className="mx-3 md:mx-6 mb-2">
          <button
            onClick={onOpenMap}
            className="w-full py-3 px-4 bg-govgreen text-white rounded-xl font-semibold flex items-center justify-center gap-2 hover:bg-govgreen/90 shadow-sm"
          >
            <MapPin size={20} />
            <span>{t("chat.openMap")}</span>
          </button>
        </div>
      )}

      {voiceError && (
        <div className="mx-3 md:mx-6 mb-1 text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-lg">
          {voiceError}
        </div>
      )}

      <div className="px-3 md:px-6 pb-3 pt-2 border-t border-gray-200 bg-white">
        <div className="flex items-end gap-2">
          <button
            onMouseDown={startVoice}
            onMouseUp={stopVoice}
            onMouseLeave={stopVoice}
            onTouchStart={(e) => { e.preventDefault(); startVoice(); }}
            onTouchEnd={(e) => { e.preventDefault(); stopVoice(); }}
            title="Hold to speak"
            className={`shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all select-none ${
              listening
                ? "bg-red-500 text-white scale-110 animate-pulse"
                : "bg-saffron/10 text-saffron hover:bg-saffron/20 active:bg-red-400 active:text-white active:scale-110"
            }`}
          >
            {listening ? <MicOff size={22} /> : <Mic size={22} />}
          </button>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={listening ? "🎤 Listening... speak now" : t("chat.placeholder")}
            rows={1}
            className={`flex-1 resize-none border rounded-2xl px-4 py-3 text-sm md:text-base focus:outline-none max-h-32 transition-colors ${
              listening
                ? "border-red-300 bg-red-50 focus:border-red-400"
                : "border-gray-300 focus:border-ashok"
            }`}
          />

          <button
            onClick={submit}
            disabled={!text.trim() || busy}
            className="shrink-0 w-12 h-12 rounded-full bg-ashok text-white flex items-center justify-center disabled:bg-gray-300 hover:bg-ashok/90 transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
        {listening && (
          <p className="text-xs text-center text-red-500 mt-1 font-medium">
            🔴 Recording... release button to stop
          </p>
        )}
      </div>
    </section>
  );
}
