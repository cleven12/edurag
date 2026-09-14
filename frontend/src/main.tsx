import { createRoot } from "react-dom/client";
import App from "./App";

const rootEl = document.getElementById("edurag-chat-root");
if (rootEl) {
  createRoot(rootEl).render(<App />);
}
