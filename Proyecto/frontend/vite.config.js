// vite.config.js
// eslint-disable-next-line no-unused-vars
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default ({ mode }) => {
  const isProd = mode === "production";

  return defineConfig({
    plugins: [react()],
    // ✅ En dev = "/", en prod = "/static/"
    base: isProd ? "/static/" : "/",

    server: {
      port: 5173,
      open: true, // abrirá http://localhost:5173/ (no /static/)
      proxy: {
        "/api": "http://127.0.0.1:8000",
        "/auth": "http://127.0.0.1:8000",
      },
    },

    // ✅ Cuando hagas build, deja los archivos donde Django los sirve
    // (ajusta esta ruta a tu estructura real)
    build: {
      outDir: "../backend/static",
      emptyOutDir: true,
    },
  });
};
