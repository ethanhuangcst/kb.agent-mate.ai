import { describe, expect, it } from "vitest";
import { buildContentSecurityPolicy } from "../lib/csp";

describe("buildContentSecurityPolicy", () => {
  it("should_include_nonce_and_strict_dynamic_when_production", () => {
    const csp = buildContentSecurityPolicy("abc123", { isDev: false });
    expect(csp).toContain("script-src");
    expect(csp).toContain("'nonce-abc123'");
    expect(csp).toContain("'strict-dynamic'");
    expect(csp).not.toContain("'unsafe-eval'");
    expect(csp).toContain("upgrade-insecure-requests");
  });

  it("should_not_allow_data_or_unsafe_inline_in_script_src", () => {
    const csp = buildContentSecurityPolicy("n", { isDev: false });
    const scriptSrc = csp.split(";").map((d) => d.trim()).find((d) => d.startsWith("script-src"));
    expect(scriptSrc).toBeDefined();
    expect(scriptSrc).not.toMatch(/data:/);
    expect(scriptSrc).not.toContain("'unsafe-inline'");
  });

  it("should_restrict_connect_src_to_self_when_production", () => {
    const csp = buildContentSecurityPolicy("n", { isDev: false });
    expect(csp).toMatch(/connect-src 'self'(;|$)/);
  });

  it("should_allow_unsafe_eval_and_ws_when_development", () => {
    const csp = buildContentSecurityPolicy("devnonce", { isDev: true });
    expect(csp).toContain("'unsafe-eval'");
    expect(csp).toContain("ws:");
    expect(csp).toContain("wss:");
    expect(csp).not.toContain("upgrade-insecure-requests");
  });

  it("should_set_frame_ancestors_none_and_object_src_none", () => {
    const csp = buildContentSecurityPolicy("n", { isDev: false });
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
  });
});
