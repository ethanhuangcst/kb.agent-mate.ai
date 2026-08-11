import { describe, expect, it } from "vitest";
import zh from "../messages/zh-CN.json";
import en from "../messages/en.json";

describe("i18n catalogs", () => {
  it("should_share_same_key_tree_for_zh_and_en", () => {
    const flatten = (obj: Record<string, unknown>, prefix = ""): string[] =>
      Object.keys(obj).flatMap((k) => {
        const path = prefix ? `${prefix}.${k}` : k;
        const v = obj[k];
        if (v && typeof v === "object" && !Array.isArray(v)) {
          return flatten(v as Record<string, unknown>, path);
        }
        return [path];
      });
    expect(flatten(zh as Record<string, unknown>).sort()).toEqual(
      flatten(en as Record<string, unknown>).sort(),
    );
  });

  it("should_keep_footer_copyright_stable", () => {
    expect(zh.footerCopyright).toBe("copyright ® Ethan Huang");
    expect(en.footerCopyright).toBe("copyright ® Ethan Huang");
  });

  it("should_expose_contact_admin_rich_tag_in_login_lead", () => {
    expect(zh.login.lead).toContain("<contact>");
    expect(en.login.lead).toContain("<contact>");
    expect(zh.login.wechatQrAlt.length).toBeGreaterThan(0);
    expect(en.login.wechatQrAlt.length).toBeGreaterThan(0);
  });
});
