import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { hashPassword } from "@/lib/passwords";
import { hashToken } from "@/lib/tokens";

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token") || "";
  if (!token) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  const tokenHash = hashToken(token);
  const rows = await sql<{ id: string; expires_at: string; used_at: string | null }[]>`
    SELECT id::text, expires_at::text, used_at::text
    FROM password_reset_tokens
    WHERE token_hash = ${tokenHash}
    LIMIT 1
  `;
  const row = rows[0];
  if (!row || row.used_at) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  if (new Date(row.expires_at).getTime() <= Date.now()) {
    return NextResponse.json({ code: "TOKEN_EXPIRED" }, { status: 400 });
  }
  return NextResponse.json({ ok: true });
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const token = String(body.token || "");
  const password = String(body.password || "");
  const confirm = String(body.confirm || "");
  if (!token) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  if (password.length < 8) {
    return NextResponse.json({ code: "PASSWORD_TOO_SHORT" }, { status: 400 });
  }
  if (password !== confirm) {
    return NextResponse.json({ code: "PASSWORD_MISMATCH" }, { status: 400 });
  }

  const tokenHash = hashToken(token);
  const rows = await sql<
    { id: string; admin_user_id: string; expires_at: string; used_at: string | null }[]
  >`
    SELECT id::text, admin_user_id::text, expires_at::text, used_at::text
    FROM password_reset_tokens
    WHERE token_hash = ${tokenHash}
    LIMIT 1
  `;
  const row = rows[0];
  if (!row || row.used_at) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  if (new Date(row.expires_at).getTime() <= Date.now()) {
    return NextResponse.json({ code: "TOKEN_EXPIRED" }, { status: 400 });
  }

  const passwordHash = await hashPassword(password);
  await sql.begin(async (tx) => {
    await tx`
      UPDATE password_reset_tokens
      SET used_at = now()
      WHERE id = ${row.id}::uuid AND used_at IS NULL
    `;
    await tx`
      UPDATE admin_users
      SET password_hash = ${passwordHash},
          must_change_password = false,
          session_version = session_version + 1
      WHERE id = ${row.admin_user_id}::uuid
    `;
  });

  return NextResponse.json({ ok: true });
}
