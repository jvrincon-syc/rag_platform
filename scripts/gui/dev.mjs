import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function resolveNpmCommand(_platform = process.platform) {
  return "npm";
}

export function buildSpawnOptions(platform = process.platform) {
  const options = { stdio: "inherit" };
  if (platform === "win32") {
    return { ...options, shell: true };
  }
  return options;
}

export function startGuiDev({ spawnFn = spawn, platform = process.platform } = {}) {
  const npmCommand = resolveNpmCommand(platform);
  const spawnOptions = buildSpawnOptions(platform);
  const api = spawnFn(npmCommand, ["run", "gui:api"], spawnOptions);
  const front = spawnFn(npmCommand, ["run", "gui:front"], spawnOptions);

  const stop = () => {
    api.kill("SIGTERM");
    front.kill("SIGTERM");
  };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
  return { api, front, stop };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  startGuiDev();
}
