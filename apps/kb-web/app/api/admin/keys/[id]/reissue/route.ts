import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { apiKeyPepper, encryptApiKey, generateApiKey, hashApiKey } from "@/lib/api-keys";
import { canAccessAdminApis, getSession } from "@/lib/session";

type Ctx = { params: Promise<{ id: string }> };

export async function POST(_req: NextRequest, ctx: Ctx) {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const { id } = await ctx.params;

  const existing = await sql<{ user_id: string; display_name: string }[]>`
    SELECT k.user_id::text AS user_id, u.display_name
    FROM api_keys k
    JOIN users u ON u.id = k.user_id
    WHERE k.id = ${id}::uuid
    LIMIT 1
  `;
  if (!existing[0]) {
    return NextResponse.json({ code: "NOT_FOUND" }, { status: 404 });
  }

  const { raw, prefix } = generateApiKey();
  const keyHash = hashApiKey(raw, apiKeyPepper());
  const keyCiphertext = encryptApiKey(raw);
  const userId = existing[0].user_id;

  const result = await sql.begin(async (tx) => {
    await tx`
      UPDATE api_keys
      SET status = 'revoked', revoked_at = NOW()
      WHERE user_id = ${userId}::uuid AND status = 'active'
    `;
    const keys = await tx<{ id: string }[]>`
      INSERT INTO api_keys (id, user_id, key_hash, key_prefix, key_ciphertext, status)
      VALUES (gen_random_uuid(), ${userId}::uuid, ${keyHash}, ${prefix}, ${keyCiphertext}, 'active')
      RETURNING id::text
    `;
    return keys[0].id;
  });

  return NextResponse.json({
    userId,
    keyId: result,
    keyPrefix: prefix,
    apiKey: raw,
    displayName: existing[0].display_name,
  });
}
