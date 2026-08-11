import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import type { SessionPayload } from "./session-types";

export type { SessionPayload } from "./session-types";
export { canAccessAdminApis } from "./auth-gate";

export const SESSION_COOKIE = "kb_admin_session";

function secretKey() {
  const secret = process.env.SESSION_SECRET || "dev-session-secret-change-me-32chars";
  return new TextEncoder().encode(secret);
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  };
}

export async function createSessionToken(payload: SessionPayload): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("7d")
    .sign(secretKey());
}

export async function readSessionToken(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, secretKey());
    return {
      adminId: String(payload.adminId),
      username: (payload.username as string | null) ?? null,
      displayName: (payload.displayName as string | null) ?? null,
      mustChangePassword: Boolean(payload.mustChangePassword),
    };
  } catch {
    return null;
  }
}

export async function getSession(): Promise<SessionPayload | null> {
  const jar = await cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  return readSessionToken(token);
}

/** Attach session cookie on a Route Handler response (reliable in Next 15). */
export async function withSessionCookie<T>(
  payload: SessionPayload,
  body: T,
  init?: { status?: number },
): Promise<NextResponse> {
  const token = await createSessionToken(payload);
  const res = NextResponse.json(body, { status: init?.status ?? 200 });
  res.cookies.set(SESSION_COOKIE, token, sessionCookieOptions());
  return res;
}

export async function clearSessionCookie(): Promise<void> {
  const jar = await cookies();
  jar.delete(SESSION_COOKIE);
}

export function clearedSessionResponse(body: unknown = { ok: true }): NextResponse {
  const res = NextResponse.json(body);
  res.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions(), maxAge: 0 });
  return res;
}
