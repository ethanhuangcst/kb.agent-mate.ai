import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { checkRateLimit } from "@/lib/rate-limit";
import { MailUnavailableError, sendPasswordResetEmail } from "@/lib/resend";
import { generateRawToken, hashToken, RESET_TOKEN_TTL_MS } from "@/lib/tokens";

function clientIp(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "unknown"
  );
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const email = String(body.email || "").trim().toLowerCase();
  if (!email || !email.includes("@")) {
    return NextResponse.json({ code: "INVALID_INPUT" }, { status: 400 });
  }

  const ip = clientIp(req);
  const limited = checkRateLimit(`forgot:${ip}:${email}`);
  if (!limited.ok) {
    return NextResponse.json(
      { code: "RATE_LIMITED", retryAfterSec: limited.retryAfterSec },
      { status: 429 },
    );
  }

  const rows = await sql<{ id: string; status: string }[]>`
    SELECT id::text, status FROM admin_users
    WHERE lower(email) = ${email}
    LIMIT 1
  `;
  const admin = rows[0];

  // Always generic success to avoid account enumeration — except mail failures when we do send.
  if (!admin || admin.status !== "active") {
    return NextResponse.json({ ok: true });
  }

  const raw = generateRawToken();
  const tokenHash = hashToken(raw);
  const expiresAt = new Date(Date.now() + RESET_TOKEN_TTL_MS);

  await sql`
    INSERT INTO password_reset_tokens (id, admin_user_id, token_hash, expires_at)
    VALUES (gen_random_uuid(), ${admin.id}::uuid, ${tokenHash}, ${expiresAt.toISOString()}::timestamptz)
  `;

  try {
    await sendPasswordResetEmail(email, raw);
  } catch (e) {
    if (e instanceof MailUnavailableError) {
      return NextResponse.json({ code: "MAIL_UNAVAILABLE" }, { status: 503 });
    }
    throw e;
  }

  const res = NextResponse.json({ ok: true });
  if (process.env.ENABLE_TEST_RESET === "1") {
    res.headers.set("x-debug-reset-token", raw);
  }
  return res;
}
