import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";
import { apiKeyPepper, encryptApiKey, generateApiKey, hashApiKey } from "@/lib/api-keys";
import { isEnglishDisplayName } from "@/lib/display-name";
import { canAccessAdminApis, getSession } from "@/lib/session";

export async function GET() {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const rows = await sql<
    {
      id: string;
      key_id: string;
      display_name: string;
      key_prefix: string;
      status: string;
      created_at: string;
    }[]
  >`
    SELECT
      u.id::text,
      k.id::text AS key_id,
      u.display_name,
      k.key_prefix,
      k.status,
      k.created_at::text
    FROM users u
    JOIN api_keys k ON k.user_id = u.id
    WHERE k.status = 'active'
    ORDER BY k.created_at DESC
  `;
  return NextResponse.json({ users: rows });
}

export async function POST(req: NextRequest) {
  const session = await getSession();
  if (!canAccessAdminApis(session)) {
    return NextResponse.json({ code: "UNAUTHORIZED" }, { status: 401 });
  }
  const body = await req.json().catch(() => ({}));
  const displayName = String(body.displayName || "").trim();
  if (!isEnglishDisplayName(displayName)) {
    return NextResponse.json({ code: "INVALID_INPUT" }, { status: 400 });
  }

  const { raw, prefix } = generateApiKey();
  const keyHash = hashApiKey(raw, apiKeyPepper());
  const keyCiphertext = encryptApiKey(raw);

  const inserted = await sql.begin(async (tx) => {
    const users = await tx<{ id: string }[]>`
      INSERT INTO users (id, display_name, status)
      VALUES (gen_random_uuid(), ${displayName}, 'active')
      RETURNING id::text
    `;
    const userId = users[0].id;
    const keys = await tx<{ id: string }[]>`
      INSERT INTO api_keys (id, user_id, key_hash, key_prefix, key_ciphertext, status)
      VALUES (gen_random_uuid(), ${userId}::uuid, ${keyHash}, ${prefix}, ${keyCiphertext}, 'active')
      RETURNING id::text
    `;
    return { userId, keyId: keys[0].id };
  });

  return NextResponse.json({
    userId: inserted.userId,
    keyId: inserted.keyId,
    keyPrefix: prefix,
    apiKey: raw,
  });
}
