import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { usePollingLoop } from "./usePollingLoop.js";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((innerResolve) => {
    resolve = innerResolve;
  });
  return { promise, resolve };
}

function PollingProbe({
  fetchOnce,
}: {
  fetchOnce: (signal: AbortSignal) => Promise<{ done: boolean }>;
}) {
  const state = usePollingLoop({
    resourceId: "resource-1",
    intervalMs: 25,
    fetchOnce,
    isTerminal: (value) => value.done,
  });

  return <span>{state.polling ? "polling" : "idle"}</span>;
}

describe("usePollingLoop", () => {
  it("no solapa solicitudes mientras una consulta sigue pendiente", async () => {
    const first = deferred<{ done: boolean }>();
    const second = deferred<{ done: boolean }>();
    let active = 0;
    let maxActive = 0;
    const fetchOnce = vi.fn((_signal: AbortSignal) => {
      active += 1;
      maxActive = Math.max(maxActive, active);
      const current = fetchOnce.mock.calls.length === 1 ? first : second;
      return current.promise.finally(() => {
        active -= 1;
      });
    });

    render(<PollingProbe fetchOnce={fetchOnce} />);

    await waitFor(() => expect(fetchOnce).toHaveBeenCalledTimes(1));
    await new Promise((resolve) => window.setTimeout(resolve, 75));
    expect(fetchOnce).toHaveBeenCalledTimes(1);

    first.resolve({ done: false });
    await waitFor(() => expect(fetchOnce).toHaveBeenCalledTimes(2));

    second.resolve({ done: true });
    await waitFor(() => expect(screen.getByText("idle")).toBeTruthy());
    expect(maxActive).toBe(1);
  });
});
