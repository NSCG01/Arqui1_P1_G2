import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/sensors": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
      "/stats": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
      "/commands": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
      "/messages": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
      "/events": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
    },
  },
});