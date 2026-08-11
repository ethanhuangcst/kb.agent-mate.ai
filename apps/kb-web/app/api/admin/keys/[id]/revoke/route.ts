import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { canAccessAdminApis, getSession } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

/** Revoke key (Agent rejects immediately). Row leaves the active users list; knowledge kept. */
export async function POST(_req: NextRequest, ctx: Ctx) {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const { id } = await ctx.params;
  await sql.begin(async (tx) => {
    const keys = await tx<{ user_id: string }[]>`
      UPDATE api_keys
      SET status = 'revoked', revoked_at = NOW()
      WHERE id = ${id}::uuid AND status = 'active'
      RETURNING user_id::text
    `;
    if (keys[0]) {
      await tx`
        UPDATE users
        SET status = 'disabled'
        WHERE id = ${keys[0].user_id}::uuid
      `;
    }
  });
  return NextResponse.json({ ok: true });
}
