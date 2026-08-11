/** Pure rules for admin delete (web-acct-08). */

export function canDeleteAdmin(opts: {
  actorId: string;
  targetId: string;
  activeCount: number;
}): { ok: true } | { ok: false; code: "CANNOT_DELETE_SELF" | "CANNOT_DELETE_LAST_ADMIN" } {
  if (opts.actorId === opts.targetId) {
    return { ok: false, code: "CANNOT_DELETE_SELF" };
  }
  if (opts.activeCount <= 1) {
    return { ok: false, code: "CANNOT_DELETE_LAST_ADMIN" };
  }
  return { ok: true };
}
