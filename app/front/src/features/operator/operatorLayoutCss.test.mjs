import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../../styles/operator.css", import.meta.url), "utf8");

async function test(name, assertion) {
  try {
    await assertion();
    console.log(`ok - ${name}`);
  } catch (error) {
    console.error(`not ok - ${name}`);
    throw error;
  }
}

await test("operator rail reserva ancho para tarjeta de sesion y logout", async () => {
  assert.match(
    css,
    /\.operator-shell\s*{[^}]*grid-template-columns:\s*minmax\(176px,\s*12vw\)\s+minmax\(0,\s*1fr\)/s,
  );
  assert.doesNotMatch(
    css,
    /@media \(max-width:\s*1180px\)[\s\S]*?\.operator-shell\s*{[^}]*grid-template-columns:/s,
  );
  assert.match(
    css,
    /@media \(max-width:\s*760px\)[\s\S]*?\.operator-shell\s*{[^}]*display:\s*block/s,
  );
});
