import { sql } from "./db";
import { hashPassword } from "./passwords";

const DEFAULT_SEED_EMAIL = "me@ethanhuang.com";

export function seedAdminEmail(): string {
  const fromEnv = (process.env.BOOTSTRAP_ADMIN_EMAIL || "").trim();
  return fromEnv || DEFAULT_SEED_EMAIL;
}

export async function ensureSeedAdmin(): Promise<{ created: boolean }> {
  const rows = await sql<{ count: string }[]>`
    SELECT COUNT(*)::text AS count FROM admin_users
  `;
  const count = Number(rows[0]?.count ?? 0);
  if (count > 0) return { created: false };

  const passwordHash = await hashPassword("admin");
  const email = seedAdminEmail();
  await sql`
    INSERT INTO admin_users (id, username, email, display_name, password_hash, must_change_password, status, session_version)
    VALUES (gen_random_uuid(), 'admin', ${email}, 'Admin', ${passwordHash}, true, 'active', 0)
  `;
  return { created: true };
}
