import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: ".",
  publicDir: "public",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        import: resolve(__dirname, "import.html"),
        library: resolve(__dirname, "library.html"),
        author: resolve(__dirname, "author.html"),
        session: resolve(__dirname, "session.html"),
      },
    },
  },
  server: {
    port: 8765,
    open: "/",
  },
});
