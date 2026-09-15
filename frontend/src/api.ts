export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatResponse =
  | { ok: true; session_id: string; message: ChatMessage }
  | { ok: false; error: string };

// Relative path: works whether the widget is served by the same Flask app
// (the default) or a proxy in front of it.
const CHAT_ENDPOINT = "/chat";

export async function sendChatMessage(
  message: string,
  sessionId: string | null,
): Promise<ChatResponse> {
  const res = await fetch(CHAT_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionId ? { message, session_id: sessionId } : { message }),
  });
  return res.json();
}
