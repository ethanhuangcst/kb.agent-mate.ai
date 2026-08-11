import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { canAccessAdminApis, getSession } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Revoke the user's active key(s).
 * Resolve user via the given key id (any status), then soft-revoke all active
 * keys for that user — so a stale pre-reissue id still disables access.
 */
export async function POST(_req: NextRequest, ctx: Ctx) {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const { id } = await ctx.params;
  await sql.begin(async (tx) => {
    const found = await tx<{ user_id: string }[]>`
      SELECT user_id::text AS user_id
      FROM api_keys
      WHERE id = ${id}::uuid
      LIMIT 1
    `;
    if (!found[0]) {
      return;
    }
    const userId = found[0].user_id;
    await tx`
      UPDATE api_keys
      SET status = 'revoked', revoked_at = NOW()
      WHERE user_id = ${userId}::uuid AND status = 'active'
    `;
    await tx`
      UPDATE users
      SET status = 'disabled'
      WHERE id = ${userId}::uuid
    `;
  });
  return NextResponse.json({ ok: true });
}
