import eslintRecommended from '@eslint/js';
import { readFile } from 'node:fs/promises';
import { parse } from 'acorn';
import { ESLint } from 'eslint';
import globals from 'globals';

const pages = [
  { path: 'web/sender.html', ecmaVersion: 'latest' },
  { path: 'web/receiver.html', ecmaVersion: 5 },
  { path: 'web/latency.html', ecmaVersion: 'latest' },
];

function inlineScripts(html) {
  return [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/giu)]
    .map((match) => match[1])
    .filter((source) => source.trim());
}

for (const page of pages) {
  const html = await readFile(page.path, 'utf8');
  const scripts = inlineScripts(html);
  if (scripts.length === 0) {
    throw new Error(`${page.path}: no inline script found`);
  }
  for (const [index, source] of scripts.entries()) {
    try {
      parse(source, {
        allowHashBang: false,
        ecmaVersion: page.ecmaVersion,
        sourceType: 'script',
      });
    } catch (error) {
      error.message = `${page.path} inline script ${index + 1}: ${error.message}`;
      throw error;
    }
    const eslint = new ESLint({
      overrideConfigFile: true,
      overrideConfig: {
        languageOptions: {
          ecmaVersion: page.ecmaVersion,
          sourceType: 'script',
          globals: {
            ...globals.browser,
            Promise: 'readonly',
          },
        },
        rules: {
          ...eslintRecommended.configs.recommended.rules,
          'no-empty': ['error', { allowEmptyCatch: true }],
          'no-redeclare': ['error', { builtinGlobals: false }],
          // Inline page scripts intentionally keep a few compatibility bindings;
          // syntax, undefined names, and correctness rules remain enforced.
          'no-unused-vars': 'off',
        },
      },
    });
    const [result] = await eslint.lintText(source, {
      filePath: `${page.path.replace(/[^a-z0-9]/giu, '-')}-${index + 1}.js`,
      warnIgnored: false,
    });
    if (result.errorCount || result.warningCount) {
      const detail = result.messages
        .map((message) => `${page.path}:${message.line}:${message.column}: ${message.message} (${message.ruleId ?? 'parse'})`)
        .join('\n');
      throw new Error(detail);
    }
  }
  console.log(`${page.path}: ${scripts.length} inline script${scripts.length === 1 ? '' : 's'} parsed and linted as ECMAScript ${page.ecmaVersion}`);
}
