import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { isEnglishDisplayName } from "@/lib/display-name";
import { hashPassword } from "@/lib/passwords";
import { withSessionCookie } from "@/lib/session";
import { hashToken } from "@/lib/tokens";
import { isValidUsername, normalizeUsername } from "@/lib/username";

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token") || "";
  if (!token) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  const tokenHash = hashToken(token);
  const rows = await sql<{ email: string; expires_at: string; used_at: string | null }[]>`
    SELECT email, expires_at::text, used_at::text
    FROM admin_invites
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
  return NextResponse.json({ email: row.email });
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const token = String(body.token || "");
  const username = normalizeUsername(String(body.username || ""));
  const displayName = String(body.displayName || "").trim();
  const password = String(body.password || "");
  const confirm = String(body.confirm || "");

  if (!token) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  if (!isValidUsername(username)) {
    return NextResponse.json({ code: "USERNAME_INVALID" }, { status: 400 });
  }
  if (!isEnglishDisplayName(displayName)) {
    return NextResponse.json({ code: "NAME_INVALID" }, { status: 400 });
  }
  if (password.length < 8) {
    return NextResponse.json({ code: "PASSWORD_TOO_SHORT" }, { status: 400 });
  }
  if (password !== confirm) {
    return NextResponse.json({ code: "PASSWORD_MISMATCH" }, { status: 400 });
  }

  const tokenHash = hashToken(token);
  const invites = await sql<
    { id: string; email: string; expires_at: string; used_at: string | null }[]
  >`
    SELECT id::text, email, expires_at::text, used_at::text
    FROM admin_invites
    WHERE token_hash = ${tokenHash}
    LIMIT 1
  `;
  const invite = invites[0];
  if (!invite || invite.used_at) {
    return NextResponse.json({ code: "INVALID_TOKEN" }, { status: 400 });
  }
  if (new Date(invite.expires_at).getTime() <= Date.now()) {
    return NextResponse.json({ code: "TOKEN_EXPIRED" }, { status: 400 });
  }

  const existing = await sql<{ id: string; status: string }[]>`
    SELECT id::text, status FROM admin_users WHERE lower(email) = ${invite.email.toLowerCase()} LIMIT 1
  `;
  if (existing[0]?.status === "active") {
    return NextResponse.json({ code: "EMAIL_TAKEN" }, { status: 409 });
  }

  const usernameClash = await sql<{ id: string }[]>`
    SELECT id::text FROM admin_users
    WHERE username IS NOT NULL AND lower(username) = ${username.toLowerCase()}
    LIMIT 1
  `;
  if (usernameClash[0] && usernameClash[0].id !== existing[0]?.id) {
    return NextResponse.json({ code: "USERNAME_TAKEN" }, { status: 409 });
  }

  const passwordHash = await hashPassword(password);
  const created = await sql.begin(async (tx) => {
    let rows: {
      id: string;
      username: string | null;
      display_name: string | null;
      session_version: number;
    }[];
    if (existing[0]?.status === "disabled") {
      rows = await tx`
        UPDATE admin_users
        SET username = ${username},
            display_name = ${displayName},
            password_hash = ${passwordHash},
            must_change_password = false,
            status = 'active',
            session_version = session_version + 1,
            email_verified_at = now()
        WHERE id = ${existing[0].id}::uuid
        RETURNING id::text, username, display_name, session_version
      `;
    } else {
      rows = await tx`
        INSERT INTO admin_users (
          id, username, email, display_name, password_hash,
          must_change_password, status, session_version, email_verified_at
        )
        VALUES (
          gen_random_uuid(), ${username}, ${invite.email}, ${displayName}, ${passwordHash},
          false, 'active', 0, now()
        )
        RETURNING id::text, username, display_name, session_version
      `;
    }
    await tx`
      UPDATE admin_invites SET used_at = now()
      WHERE id = ${invite.id}::uuid AND used_at IS NULL
    `;
    return rows[0];
  });

  if (!created) {
    return NextResponse.json({ code: "CREATE_FAILED" }, { status: 500 });
  }

  return withSessionCookie(
    {
      adminId: created.id,
      username: created.username,
      displayName: created.display_name,
      mustChangePassword: false,
      sessionVersion: Number(created.session_version),
    },
    { ok: true, displayName: created.display_name },
  );
}
