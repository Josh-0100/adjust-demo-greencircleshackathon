import { defineConfig } from 'vitest/config';
import { resolve } from 'node:path';
export default defineConfig({ resolve: { alias: { '@': resolve(__dirname, '.') } }, test: { environment: 'jsdom', setupFiles: ['./tests/setup.ts'], include: ['tests/**/*.test.{ts,tsx}'], exclude: ['tests/e2e/**'], restoreMocks: true, globals: true }, esbuild: { jsx: 'automatic' } });
