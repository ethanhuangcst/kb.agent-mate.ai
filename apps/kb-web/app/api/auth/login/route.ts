import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { verifyPassword } from "@/lib/passwords";
import { ensureSeedAdmin } from "@/lib/seed";
import { withSessionCookie } from "@/lib/session";

export async function POST(req: NextRequest) {
  await ensureSeedAdmin();
  const body = await req.json().catch(() => ({}));
  const login = String(body.login || "").trim();
  const password = String(body.password || "");
  if (!login || !password) {
    return NextResponse.json({ code: "INVALID_INPUT" }, { status: 400 });
  }

  const rows = await sql<
    {
      id: string;
      username: string | null;
      email: string | null;
      display_name: string | null;
      password_hash: string;
      must_change_password: boolean;
    }[]
  >`
    SELECT id::text, username, email, display_name, password_hash, must_change_password
    FROM admin_users
    WHERE username = ${login} OR email = ${login}
    LIMIT 1
  `;
  const admin = rows[0];
  if (!admin || !(await verifyPassword(password, admin.password_hash))) {
    return NextResponse.json({ code: "LOGIN_FAILED" }, { status: 401 });
  }

  return withSessionCookie(
    {
      adminId: admin.id,
      username: admin.username,
      displayName: admin.display_name,
      mustChangePassword: admin.must_change_password,
    },
    {
      mustChangePassword: admin.must_change_password,
      displayName: admin.display_name || admin.username || "Admin",
    },
  );
}
