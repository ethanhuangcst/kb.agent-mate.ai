import { createHash, randomBytes } from "crypto";

export function hashApiKey(rawKey: string, pepper: string): string {
  return createHash("sha256").update(`${pepper}${rawKey}`, "utf8").digest("hex");
}

export function generateApiKey(): { raw: string; prefix: string } {
  const raw = `kb_live_${randomBytes(24).toString("hex")}`;
  const prefix = raw.slice(0, 12);
  return { raw, prefix };
}

export function apiKeyPepper(): string {
  return process.env.API_KEY_PEPPER || "dev-api-key-pepper-change-me";
}
