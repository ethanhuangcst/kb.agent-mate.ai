import { createCipheriv, createDecipheriv, createHash, randomBytes } from "crypto";

const AES_ALGO = "aes-256-gcm";
const IV_BYTES = 12;
const TAG_BYTES = 16;

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

/** Prefer API_KEY_ENCRYPTION_SECRET; local may fall back to pepper (ADR-007). */
export function apiKeyEncryptionSecret(): string {
  const explicit = process.env.API_KEY_ENCRYPTION_SECRET?.trim();
  if (explicit) return explicit;
  return apiKeyPepper();
}

function deriveAesKey(secret: string): Buffer {
  return createHash("sha256").update(secret, "utf8").digest();
}

/** Encrypt plaintext API key for `key_ciphertext` (`v1:` + base64url(iv|tag|ct)). */
export function encryptApiKey(plaintext: string, secret = apiKeyEncryptionSecret()): string {
  const iv = randomBytes(IV_BYTES);
  const cipher = createCipheriv(AES_ALGO, deriveAesKey(secret), iv);
  const enc = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `v1:${Buffer.concat([iv, tag, enc]).toString("base64url")}`;
}

export function decryptApiKey(ciphertext: string, secret = apiKeyEncryptionSecret()): string {
  if (!ciphertext.startsWith("v1:")) {
    throw new Error("UNSUPPORTED_CIPHERTEXT");
  }
  const buf = Buffer.from(ciphertext.slice(3), "base64url");
  if (buf.length < IV_BYTES + TAG_BYTES + 1) {
    throw new Error("INVALID_CIPHERTEXT");
  }
  const iv = buf.subarray(0, IV_BYTES);
  const tag = buf.subarray(IV_BYTES, IV_BYTES + TAG_BYTES);
  const data = buf.subarray(IV_BYTES + TAG_BYTES);
  const decipher = createDecipheriv(AES_ALGO, deriveAesKey(secret), iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(data), decipher.final()]).toString("utf8");
}
