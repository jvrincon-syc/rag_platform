import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(
  "src/features/platform/PlatformWorkspace.tsx",
  "utf8",
);
const navigation = readFileSync(
  "src/features/platform/platformNavigation.ts",
  "utf8",
);

test("Platform pipeline views mount the project-scoped legacy pipeline host", () => {
  assert.match(source, /PlatformLegacyPipelineWorkspace/);
  assert.doesNotMatch(navigation, /read-only|solo lectura/i);
});

test("Pipeline nav entries derive from the Legacy dashboard contracts, not hand copies", () => {
  assert.match(
    navigation,
    /dashboardNavigation/,
    "platformNavigation.ts must import DASHBOARD_VIEWS instead of duplicating labels",
  );
  assert.doesNotMatch(
    navigation,
    /Operación|Revisión/,
    "pipeline labels must come verbatim from DASHBOARD_VIEWS sidebarLabels",
  );
});
