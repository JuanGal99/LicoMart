import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/usuarios": "http://localhost:8000",
      "/productos": "http://localhost:8000",
      "/carrito": "http://localhost:8000",
      "/pedidos": "http://localhost:8000",
      "/media": "http://localhost:8000",
    },
  },
});
