import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { reconcileCurrentUser } from "../src/lib/current-user-cache.ts";

interface User {
  id: string;
  display_name: string | null;
}

describe("reconcileCurrentUser", () => {
  it("resolves with the fresh user and does not reload on first load (no previous id)", async () => {
    let reloadCalls = 0;
    const freshUser: User = { id: "user-1", display_name: "First" };

    const result = await reconcileCurrentUser(undefined, freshUser, () => {
      reloadCalls += 1;
    });

    assert.equal(reloadCalls, 0);
    assert.deepEqual(result, freshUser);
  });

  it("resolves with the fresh user and does not reload when identity is unchanged", async () => {
    let reloadCalls = 0;
    const freshUser: User = { id: "user-1", display_name: "First Updated" };

    const result = await reconcileCurrentUser("user-1", freshUser, () => {
      reloadCalls += 1;
    });

    assert.equal(reloadCalls, 0);
    assert.deepEqual(result, freshUser);
  });

  it("triggers a reload and never resolves when identity changes", async () => {
    let reloadCalls = 0;
    const freshUser: User = { id: "user-2", display_name: "Second" };

    const pending = reconcileCurrentUser("user-1", freshUser, () => {
      reloadCalls += 1;
    });

    const outcome = await Promise.race([
      pending.then(() => "resolved"),
      new Promise((resolve) => setTimeout(() => resolve("timed-out"), 50)),
    ]);

    assert.equal(reloadCalls, 1);
    assert.equal(outcome, "timed-out");
  });
});
