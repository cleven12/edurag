import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds a single self-mounting widget bundle straight into Flask's static
// folder, so the backend can serve it with a plain <script>/<link> tag —
// no separate frontend server or asset pipeline needed at runtime.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../app/static/widget",
    emptyOutDir: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: "src/main.tsx",
      output: {
        entryFileNames: "widget.js",
        assetFileNames: "widget.[ext]",
      },
    },
  },
});
