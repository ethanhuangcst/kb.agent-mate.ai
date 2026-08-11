import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { hashPassword } from "@/lib/passwords";
import { getSession, withSessionCookie } from "@/lib/session";

export async function POST(req: NextRequest) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const body = await req.json().catch(() => ({}));
  const password = String(body.password || "");
  const confirm = String(body.confirm || "");
  if (password.length < 8) {
    return NextResponse.json({ code: "PASSWORD_TOO_SHORT" }, { status: 400 });
  }
  if (password !== confirm) {
    return NextResponse.json({ code: "PASSWORD_MISMATCH" }, { status: 400 });
  }

  const passwordHash = await hashPassword(password);
  await sql`
    UPDATE admin_users
    SET password_hash = ${passwordHash}, must_change_password = false
    WHERE id = ${session.adminId}::uuid
  `;

  return withSessionCookie(
    {
      ...session,
      mustChangePassword: false,
    },
    { ok: true },
  );
}
