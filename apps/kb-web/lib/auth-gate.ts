import type { SessionPayload } from "./session-types";

export type { SessionPayload } from "./session-types";

export function canAccessAdminApis(session: SessionPayload | null): boolean {
  return Boolean(session && !session.mustChangePassword);
}
