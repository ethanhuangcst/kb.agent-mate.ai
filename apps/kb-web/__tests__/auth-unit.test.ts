import { describe, expect, it } from "vitest";
import { hashApiKey, generateApiKey, encryptApiKey, decryptApiKey } from "../lib/api-keys";
import { canAccessAdminApis } from "../lib/auth-gate";
import type { SessionPayload } from "../lib/session-types";
import { hashPassword, verifyPassword } from "../lib/passwords";
import { isEnglishDisplayName } from "../lib/display-name";

describe("api keys", () => {
  it("should_hash_stably_when_pepper_fixed", () => {
    const a = hashApiKey("kb_live_abc", "pepper");
    const b = hashApiKey("kb_live_abc", "pepper");
    expect(a).toBe(b);
    expect(a).not.toBe(hashApiKey("kb_live_abc", "other"));
  });

  it("should_generate_kb_live_prefix", () => {
    const { raw, prefix } = generateApiKey();
    expect(raw.startsWith("kb_live_")).toBe(true);
    expect(prefix).toBe(raw.slice(0, 12));
  });

  it("should_roundtrip_encrypt_decrypt_when_secret_fixed", () => {
    const raw = "kb_live_roundtrip_secret_value_001";
    const secret = "test-encryption-secret-32chars!!";
    const ct = encryptApiKey(raw, secret);
    expect(ct.startsWith("v1:")).toBe(true);
    expect(ct).not.toContain(raw);
    expect(decryptApiKey(ct, secret)).toBe(raw);
  });

  it("should_fail_decrypt_when_secret_differs", () => {
    const ct = encryptApiKey("kb_live_x", "secret-a");
    expect(() => decryptApiKey(ct, "secret-b")).toThrow();
  });
});

describe("display names", () => {
  it("should_accept_english_names_when_latin_letters", () => {
    expect(isEnglishDisplayName("Daniel Foster")).toBe(true);
    expect(isEnglishDisplayName("O'Neil")).toBe(true);
    expect(isEnglishDisplayName("Mary-Jane")).toBe(true);
  });

  it("should_reject_non_english_or_empty_names", () => {
    expect(isEnglishDisplayName("张三")).toBe(false);
    expect(isEnglishDisplayName("User 1")).toBe(false);
    expect(isEnglishDisplayName("")).toBe(false);
    expect(isEnglishDisplayName("  ")).toBe(false);
  });
});

describe("passwords", () => {
  it("should_verify_roundtrip", async () => {
    const hash = await hashPassword("admin");
    expect(await verifyPassword("admin", hash)).toBe(true);
    expect(await verifyPassword("wrong", hash)).toBe(false);
  });
});

describe("session gate", () => {
  it("should_block_admin_apis_when_must_change_password", () => {
    const session: SessionPayload = {
      adminId: "1",
      username: "admin",
      displayName: "Admin",
      mustChangePassword: true,
    };
    expect(canAccessAdminApis(session)).toBe(false);
    expect(canAccessAdminApis({ ...session, mustChangePassword: false })).toBe(true);
    expect(canAccessAdminApis(null)).toBe(false);
  });
});
