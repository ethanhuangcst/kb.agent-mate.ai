import { NextRequest, NextResponse } from "next/server";
import { canDeleteAdmin } from "@/lib/admin-rules";
import { sql } from "@/lib/db";
import { canAccessAdminApis, getSession } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

export async function DELETE(_req: NextRequest, ctx: Ctx) {
  const session = await getSession();
  if (!canAccessAdminApis(session) || !session) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const { id } = await ctx.params;
  if (!id) {
    return NextResponse.json({ code: "INVALID_INPUT" }, { status: 400 });
  }

  const target = await sql<{ id: string; status: string }[]>`
    SELECT id::text, status FROM admin_users WHERE id = ${id}::uuid LIMIT 1
  `;
  if (!target[0] || target[0].status !== "active") {
    return NextResponse.json({ code: "NOT_FOUND" }, { status: 404 });
  }

  const counts = await sql<{ n: string }[]>`
    SELECT count(*)::text AS n FROM admin_users WHERE status = 'active'
  `;
  const activeCount = Number(counts[0]?.n || 0);
  const gate = canDeleteAdmin({
    actorId: session.adminId,
    targetId: id,
    activeCount,
  });
  if (!gate.ok) {
    return NextResponse.json({ code: gate.code }, { status: 400 });
  }

  await sql`
    UPDATE admin_users
    SET status = 'disabled', session_version = session_version + 1
    WHERE id = ${id}::uuid AND status = 'active'
  `;

  return NextResponse.json({ ok: true });
}
