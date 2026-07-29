import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    // Baked in (not just a CLI flag) so a plain `npm run dev`, run by
    // anything - a terminal, a VS Code task, an editor's own auto-start -
    // always binds to every interface. The Nginx container in infra/ can
    // only reach the Vite dev server if it's not loopback-only, and that
    // has been the recurring cause of 502s on http://localhost:8080/.
    host: true,
    port: 5173,
    strictPort: true,
  },
});
