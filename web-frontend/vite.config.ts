import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    strictPort: true,
    // Polling avoids inotify EIO inside Docker on macOS bind mounts
    watch: {
      usePolling: true,
      interval: 1000,
    },
    hmr: {
      overlay: false,
      host: "localhost",
      clientPort: 5173,
    },
    fs: {
      strict: false,
    },
  },
});
