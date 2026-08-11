import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { decryptApiKey } from "@/lib/api-keys";
import { canAccessAdminApis, getSession } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, ctx: Ctx) {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const { id } = await ctx.params;

  const rows = await sql<
    {
      key_id: string;
      key_prefix: string;
      status: string;
      key_ciphertext: string | null;
      display_name: string;
    }[]
  >`
    SELECT
      k.id::text AS key_id,
      k.key_prefix,
      k.status,
      k.key_ciphertext,
      u.display_name
    FROM api_keys k
    JOIN users u ON u.id = k.user_id
    WHERE k.id = ${id}::uuid
    LIMIT 1
  `;
  const row = rows[0];
  if (!row) {
    return NextResponse.json({ code: "NOT_FOUND" }, { status: 404 });
  }
  if (row.status !== "active") {
    return NextResponse.json({ code: "KEY_REVOKED" }, { status: 410 });
  }
  if (!row.key_ciphertext) {
    return NextResponse.json({ code: "CIPHERTEXT_MISSING" }, { status: 409 });
  }

  let apiKey: string;
  try {
    apiKey = decryptApiKey(row.key_ciphertext);
  } catch {
    return NextResponse.json({ code: "DECRYPT_FAILED" }, { status: 500 });
  }

  return NextResponse.json({
    keyId: row.key_id,
    keyPrefix: row.key_prefix,
    displayName: row.display_name,
    apiKey,
  });
}
