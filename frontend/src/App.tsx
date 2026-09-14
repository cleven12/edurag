import { useEffect, useRef, useState } from "react";
import { sendChatMessage, type ChatMessage } from "./api";
import "./widget.css";

const STORAGE_KEY = "edurag_session";
const ASSISTANT_NAME = "Claveniuz";

type DisplayMessage = ChatMessage & { typing?: boolean };

export default function App() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      role: "assistant",
      content: `Hi! I'm ${ASSISTANT_NAME}, your assistant. Ask me anything about programs, admissions, or campus life.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef<string | null>(localStorage.getItem(STORAGE_KEY));
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, open]);

  async function handleSend() {
    const question = input.trim();
    if (!question || loading) return;

    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    setMessages((m) => [...m, { role: "assistant", content: `${ASSISTANT_NAME} is typing...`, typing: true }]);

    try {
      const data = await sendChatMessage(question, sessionId.current);
      setMessages((m) => m.filter((msg) => !msg.typing));

      if (data.ok) {
        sessionId.current = data.session_id;
        localStorage.setItem(STORAGE_KEY, data.session_id);
        setMessages((m) => [...m, { role: "assistant", content: data.message.content }]);
      } else {
        setMessages((m) => [...m, { role: "assistant", content: "Sorry, something went wrong. Try again." }]);
      }
    } catch {
      setMessages((m) => m.filter((msg) => !msg.typing));
      setMessages((m) => [...m, { role: "assistant", content: "Can't reach the server right now. Please try again later." }]);
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    sessionId.current = null;
    localStorage.removeItem(STORAGE_KEY);
    setMessages([{ role: "assistant", content: "Conversation cleared. How can I help you?" }]);
  }

  return (
    <>
      <button id="edurag-btn" aria-label="Chat with the assistant" onClick={() => setOpen((o) => !o)}>
        <svg viewBox="0 0 24 24">
          <path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z" />
        </svg>
      </button>

      {open && (
        <div id="edurag-box" role="dialog" aria-label="Assistant chat">
          <div id="edurag-header">
            <div className="info">
              <div className="avatar">{ASSISTANT_NAME[0]}</div>
              <div>
                <div className="name">{ASSISTANT_NAME}</div>
                <div className="sub">Assistant</div>
              </div>
            </div>
            <button id="edurag-close" aria-label="Close" onClick={() => setOpen(false)}>
              &#x2715;
            </button>
          </div>

          <div id="edurag-messages" ref={scrollRef}>
            {messages.map((m, i) => (
              <div key={i} className={`edurag-msg ${m.role === "user" ? "user" : "bot"}${m.typing ? " typing" : ""}`}>
                {m.content}
              </div>
            ))}
          </div>

          <button id="edurag-clear" onClick={handleClear}>
            Clear conversation
          </button>

          <div id="edurag-input-row">
            <input
              id="edurag-input"
              type="text"
              placeholder="Ask something..."
              autoComplete="off"
              value={input}
              disabled={loading}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />
            <button id="edurag-send" disabled={loading} onClick={handleSend}>
              <svg viewBox="0 0 24 24">
                <path d="M2 21l21-9L2 3v7l15 2-15 2z" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
