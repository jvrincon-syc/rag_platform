import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Component tests plus plain-TS unit suites (mappers, resolvers with no JSX).
// The .mjs suites keep running under `npm test` (tsc + node) and are excluded
// here to avoid executing them twice under a different module resolution.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    // Testing Library only registers its afterEach unmount when globals exist;
    // without this, renders leak across tests.
    globals: true,
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
});
