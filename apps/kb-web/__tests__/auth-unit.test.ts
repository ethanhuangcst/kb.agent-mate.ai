import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { hashApiKey, generateApiKey, encryptApiKey, decryptApiKey } from "../lib/api-keys";
import { canAccessAdminApis } from "../lib/auth-gate";
import type { SessionPayload } from "../lib/session-types";
import { hashPassword, verifyPassword } from "../lib/passwords";
import { isEnglishDisplayName } from "../lib/display-name";
import { isValidUsername, normalizeUsername } from "../lib/username";

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

describe("usernames", () => {
  it("should_accept_valid_usernames_when_letter_start", () => {
    expect(isValidUsername("admin")).toBe(true);
    expect(isValidUsername("kbadmin")).toBe(true);
    expect(isValidUsername("Kb_Admin.1")).toBe(true);
    expect(normalizeUsername("  kbadmin  ")).toBe("kbadmin");
  });

  it("should_reject_invalid_or_empty_usernames", () => {
    expect(isValidUsername("")).toBe(false);
    expect(isValidUsername("ab")).toBe(false);
    expect(isValidUsername("1admin")).toBe(false);
    expect(isValidUsername("kb admin")).toBe(false);
    expect(isValidUsername("张三")).toBe(false);
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
      sessionVersion: 0,
    };
    expect(canAccessAdminApis(session)).toBe(false);
    expect(canAccessAdminApis({ ...session, mustChangePassword: false })).toBe(true);
    expect(canAccessAdminApis(null)).toBe(false);
  });
});

describe("tokens", () => {
  it("should_hash_tokens_stably", async () => {
    const { hashToken, generateRawToken } = await import("../lib/tokens");
    const raw = generateRawToken();
    expect(hashToken(raw)).toBe(hashToken(raw));
    expect(hashToken(raw)).not.toBe(hashToken(generateRawToken()));
  });
});

describe("rate limit", () => {
  it("should_block_when_over_limit", async () => {
    const { checkRateLimit, _resetRateLimitsForTests } = await import("../lib/rate-limit");
    _resetRateLimitsForTests();
    const key = `test:${Date.now()}`;
    for (let i = 0; i < 5; i++) {
      expect(checkRateLimit(key, 5, 60_000).ok).toBe(true);
    }
    expect(checkRateLimit(key, 5, 60_000).ok).toBe(false);
  });
});

describe("admin delete rules", () => {
  it("should_forbid_self_and_last_admin", async () => {
    const { canDeleteAdmin } = await import("../lib/admin-rules");
    expect(canDeleteAdmin({ actorId: "a", targetId: "a", activeCount: 2 }).ok).toBe(false);
    expect(canDeleteAdmin({ actorId: "a", targetId: "b", activeCount: 1 }).ok).toBe(false);
    expect(canDeleteAdmin({ actorId: "a", targetId: "b", activeCount: 2 }).ok).toBe(true);
  });
});

describe("publicAppBaseUrl", () => {
  const keys = ["PUBLIC_BASE_URL", "NEXT_PUBLIC_APP_URL", "NODE_ENV"] as const;
  const saved: Record<string, string | undefined> = {};

  beforeEach(() => {
    for (const k of keys) saved[k] = process.env[k];
  });
  afterEach(() => {
    for (const k of keys) {
      if (saved[k] === undefined) delete process.env[k];
      else process.env[k] = saved[k];
    }
  });

  it("should_prefer_public_base_url_over_next_public", async () => {
    process.env.PUBLIC_BASE_URL = "https://kb.agent-mate.ai";
    process.env.NEXT_PUBLIC_APP_URL = "http://127.0.0.1:3000";
    process.env.NODE_ENV = "production";
    const { publicAppBaseUrl } = await import("../lib/tokens");
    expect(publicAppBaseUrl()).toBe("https://kb.agent-mate.ai");
  });

  it("should_rewrite_127_to_localhost_keeping_port_when_local", async () => {
    process.env.PUBLIC_BASE_URL = "http://127.0.0.1:3000";
    delete process.env.NEXT_PUBLIC_APP_URL;
    process.env.NODE_ENV = "development";
    const { publicAppBaseUrl } = await import("../lib/tokens");
    expect(publicAppBaseUrl()).toBe("http://localhost:3000");
  });

  it("should_default_local_to_localhost_with_port_when_unset", async () => {
    delete process.env.PUBLIC_BASE_URL;
    delete process.env.NEXT_PUBLIC_APP_URL;
    process.env.NODE_ENV = "development";
    const { publicAppBaseUrl } = await import("../lib/tokens");
    expect(publicAppBaseUrl()).toBe("http://localhost:3000");
  });

  it("should_throw_when_production_base_is_loopback", async () => {
    process.env.PUBLIC_BASE_URL = "http://127.0.0.1:3000";
    process.env.NODE_ENV = "production";
    const { publicAppBaseUrl } = await import("../lib/tokens");
    expect(() => publicAppBaseUrl()).toThrow(/PUBLIC_BASE_URL/);
  });
});

describe("email log transport", () => {
  it("should_record_outbox_when_log_transport", async () => {
    process.env.EMAIL_TRANSPORT = "log";
    process.env.PUBLIC_BASE_URL = "http://127.0.0.1:3000";
    delete process.env.NEXT_PUBLIC_APP_URL;
    process.env.NODE_ENV = "development";
    const { drainLogOutbox, sendPasswordResetEmail } = await import("../lib/resend");
    drainLogOutbox();
    const url = await sendPasswordResetEmail("a@example.com", "tok123");
    expect(url).toContain("token=tok123");
    expect(url.startsWith("http://localhost:3000/reset-password?")).toBe(true);
    expect(url).not.toContain("127.0.0.1");
    const mails = drainLogOutbox();
    expect(mails).toHaveLength(1);
    expect(mails[0].kind).toBe("password_reset");
    expect(mails[0].to).toBe("a@example.com");
  });
});
