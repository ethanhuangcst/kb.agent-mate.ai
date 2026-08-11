import { NextResponse } from "next/server";
import { hashPassword } from "@/lib/passwords";
import { sql } from "@/lib/db";
import { seedAdminEmail } from "@/lib/seed";

/**
 * Test-only: reset seed admin to admin/admin with must_change_password=true.
 * Blocked in production unless ENABLE_TEST_RESET=1.
 */
export async function POST() {
  if (process.env.NODE_ENV === "production" && process.env.ENABLE_TEST_RESET !== "1") {
    return NextResponse.json({ code: "FORBIDDEN" }, { status: 403 });
  }

  const passwordHash = await hashPassword("admin");
  const email = seedAdminEmail();
  const existing = await sql<{ id: string }[]>`
    SELECT id::text FROM admin_users WHERE username = 'admin' LIMIT 1
  `;
  if (existing[0]) {
    await sql`
      UPDATE admin_users
      SET password_hash = ${passwordHash},
          must_change_password = true,
          email = ${email}
      WHERE username = 'admin'
    `;
  } else {
    await sql`
      INSERT INTO admin_users (id, username, email, display_name, password_hash, must_change_password)
      VALUES (gen_random_uuid(), 'admin', ${email}, 'Admin', ${passwordHash}, true)
    `;
  }

  // Isolate E2E: soft-revoke all keys so leftover users do not collide on display names.
  await sql`UPDATE api_keys SET status = 'revoked' WHERE status = 'active'`;
  await sql`UPDATE users SET status = 'disabled' WHERE status = 'active'`;

  return NextResponse.json({ ok: true });
}
