import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import assert from "node:assert/strict";
import test from "node:test";

const indexHtml = readFileSync(resolve("index.html"), "utf8");

test("browser tab uses the canonical RAG Platform identity", () => {
  assert.match(indexHtml, /<title>RAG Platform<\/title>/);
  assert.doesNotMatch(indexHtml, /SST Pipeline - Ingesta Fase 1/);
});
