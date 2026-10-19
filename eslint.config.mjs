import eslint from '@eslint/js';
import globals from 'globals';

export default [
  {
    ignores: [
      '.run/**',
      'dist/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
      'work/**',
    ],
  },
  eslint.configs.recommended,
  {
    files: ['scripts/**/*.mjs', 'tests/**/*.mjs', 'playwright.config.mjs'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.node,
        WebSocket: 'readonly',
      },
    },
  },
];
