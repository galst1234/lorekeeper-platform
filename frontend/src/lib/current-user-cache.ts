interface IdentifiedUser {
  id: string;
}

/**
 * Detects a change in the signed-in user (a session expired and a different account
 * signed in, in the same tab, without a full reload) and forces a full page reload
 * instead of clearing the query cache in place. Clearing the cache from inside this
 * same query's queryFn also cancels the query currently running it — and any other
 * query concurrently in flight, e.g. during a window-focus refetch-all — which either
 * throws in imperative callers or leaves other queries' observers stuck rendering
 * stale, pre-switch data (including access-controlled fields like a campaign's
 * invite_code). A reload sidesteps this: no in-memory observer survives it. The
 * returned promise never resolves on a mismatch so nothing downstream renders in the
 * brief window before the reload takes effect.
 */
export function reconcileCurrentUser<TUser extends IdentifiedUser>(
  previousUserId: string | undefined,
  me: TUser,
  reload: () => void = () => window.location.reload()
): Promise<TUser> {
  if (previousUserId !== undefined && previousUserId !== me.id) {
    reload();
    return new Promise<TUser>(() => {});
  }
  return Promise.resolve(me);
}
