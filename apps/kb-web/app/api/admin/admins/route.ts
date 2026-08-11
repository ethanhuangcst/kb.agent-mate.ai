import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { checkRateLimit } from "@/lib/rate-limit";
import { MailUnavailableError, sendAdminInviteEmail } from "@/lib/resend";
import { canAccessAdminApis, getSession } from "@/lib/session";
import { generateRawToken, hashToken, INVITE_TOKEN_TTL_MS } from "@/lib/tokens";

function clientIp(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "unknown"
  );
}

export async function GET() {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const rows = await sql<
    {
      id: string;
      username: string | null;
      email: string | null;
      display_name: string | null;
      status: string;
      created_at: string;
    }[]
  >`
    SELECT id::text, username, email, display_name, status, created_at::text
    FROM admin_users
    WHERE status = 'active'
    ORDER BY created_at ASC
  `;
  return NextResponse.json({ admins: rows });
}

export async function POST(req: NextRequest) {
  const session = await getSession();
  if (!canAccessAdminApis(session) || !session) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }

  const body = await req.json().catch(() => ({}));
  const email = String(body.email || "").trim().toLowerCase();
  if (!email || !email.includes("@")) {
    return NextResponse.json({ code: "INVALID_INPUT" }, { status: 400 });
  }

  const limited = checkRateLimit(`invite:${clientIp(req)}:${email}`);
  if (!limited.ok) {
    return NextResponse.json(
      { code: "RATE_LIMITED", retryAfterSec: limited.retryAfterSec },
      { status: 429 },
    );
  }

  const existing = await sql<{ id: string; status: string }[]>`
    SELECT id::text, status FROM admin_users WHERE lower(email) = ${email} LIMIT 1
  `;
  if (existing[0]?.status === "active") {
    return NextResponse.json({ code: "EMAIL_TAKEN" }, { status: 409 });
  }

  const raw = generateRawToken();
  const tokenHash = hashToken(raw);
  const expiresAt = new Date(Date.now() + INVITE_TOKEN_TTL_MS);

  await sql`
    INSERT INTO admin_invites (id, email, invited_by_admin_id, token_hash, expires_at)
    VALUES (gen_random_uuid(), ${email}, ${session.adminId}::uuid, ${tokenHash}, ${expiresAt.toISOString()}::timestamptz)
  `;

  try {
    await sendAdminInviteEmail(email, raw);
  } catch (e) {
    if (e instanceof MailUnavailableError) {
      return NextResponse.json({ code: "MAIL_UNAVAILABLE" }, { status: 503 });
    }
    throw e;
  }

  const res = NextResponse.json({ ok: true });
  if (process.env.ENABLE_TEST_RESET === "1") {
    res.headers.set("x-debug-invite-token", raw);
  }
  return res;
}
