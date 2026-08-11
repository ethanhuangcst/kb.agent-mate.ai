import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { sql } from "./db";
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
      sessionVersion: Number(payload.sessionVersion ?? 0),
    };
  } catch {
    return null;
  }
}

export async function getSession(): Promise<SessionPayload | null> {
  const jar = await cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  const session = await readSessionToken(token);
  if (!session) return null;

  const rows = await sql<
    {
      status: string;
      session_version: number;
      must_change_password: boolean;
      username: string | null;
      display_name: string | null;
    }[]
  >`
    SELECT status, session_version, must_change_password, username, display_name
    FROM admin_users
    WHERE id = ${session.adminId}::uuid
    LIMIT 1
  `;
  const row = rows[0];
  if (!row || row.status !== "active") return null;
  if (Number(row.session_version) !== session.sessionVersion) return null;

  return {
    adminId: session.adminId,
    username: row.username,
    displayName: row.display_name,
    mustChangePassword: row.must_change_password,
    sessionVersion: Number(row.session_version),
  };
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
