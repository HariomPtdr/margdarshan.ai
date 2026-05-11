import type { Message } from "../lib/types";

interface Props {
  message: Message;
  onChipSelect?: (value: string) => void;
}

function parseChips(content: string): { intro: string; chips: string[] } | null {
  const lines = content.split("\n").map(l => l.trim()).filter(Boolean);
  const chipLines = lines.filter(l => /^\d+\.\s/.test(l));
  if (chipLines.length < 2) return null;
  const firstIdx = lines.findIndex(l => /^\d+\.\s/.test(l));
  const intro = lines.slice(0, firstIdx).join(" ").trim();
  const chips = chipLines.map(l => l.replace(/^\d+\.\s+/, "").trim());
  return { intro, chips };
}

const F = { fontFamily:"'Inter',sans-serif", fontSize:"0.85rem", lineHeight:1.6 };

export function MessageBubble({ message, onChipSelect }: Props) {
  const isUser = message.role === "user";

  if (!isUser) {
    const parsed = onChipSelect ? parseChips(message.content) : null;
    if (parsed) {
      return (
        <div className="flex justify-start message-enter" style={{ maxWidth:"88%" }}>
          <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
            {parsed.intro && (
              <div className="bubble-bot" style={{ ...F, padding:"10px 14px", whiteSpace:"pre-line" }}>
                {parsed.intro}
              </div>
            )}
            <div style={{ display:"flex", flexWrap:"wrap", gap:6, paddingLeft:2 }}>
              {parsed.chips.map((chip, i) => (
                <button key={i} onClick={() => onChipSelect(String(i + 1))} className="chip-reply">
                  {chip}
                </button>
              ))}
            </div>
          </div>
        </div>
      );
    }
    return (
      <div className="flex justify-start message-enter">
        <div className="bubble-bot" style={{ ...F, padding:"10px 14px", maxWidth:"82%", whiteSpace:"pre-line" }}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-end message-enter">
      <div className="bubble-user" style={{ ...F, padding:"10px 14px", maxWidth:"78%" }}>
        {message.content}
      </div>
    </div>
  );
}
