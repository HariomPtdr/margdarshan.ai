import type { Message } from "../lib/types";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} message-enter`}>
      <div
        className={`max-w-[85%] md:max-w-[75%] px-4 py-2.5 rounded-2xl text-sm md:text-base leading-relaxed shadow-sm ${
          isUser
            ? "bg-ashok text-white rounded-br-sm"
            : "bg-white text-gray-900 rounded-bl-sm border border-gray-200"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
