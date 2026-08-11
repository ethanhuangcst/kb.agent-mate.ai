import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  const res = await request.post("/api/admin/test/reset-seed");
  expect(res.ok()).toBeTruthy();
});

async function loginAndUnlock(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByTestId("login-form").locator('input[name="login"]').fill("admin");
  await page.getByTestId("login-form").locator('input[name="password"]').fill("admin");
  await page.getByTestId("login-form").locator('button[type="submit"]').click();
  await page.waitForURL(/change-password/);
  await page.getByTestId("change-password-form").locator('input[name="password"]').fill("adminpass12");
  await page.getByTestId("change-password-form").locator('input[name="confirm"]').fill("adminpass12");
  await page.getByTestId("change-password-form").locator('button[type="submit"]').click();
  await page.waitForURL(/admin\/users/);
}

async function uniqueEnglishName(prefix: string): Promise<string> {
  const letters = Array.from({ length: 8 }, () =>
    String.fromCharCode(65 + Math.floor(Math.random() * 26)),
  ).join("");
  return `${prefix} ${letters}`;
}

/** NonContactTextInput starts readOnly until focus (Contacts autofill guard). */
async function fillKbUserLabel(
  page: import("@playwright/test").Page,
  name: string,
) {
  const input = page.getByTestId("issue-form").locator('input[name="kbUserLabel"]');
  await input.click();
  await input.fill(name);
}

test("should_force_password_change_then_issue_key", async ({ page }) => {
  await loginAndUnlock(page);
  await expect(page.getByTestId("issue-key")).toBeVisible();
  await page.getByTestId("issue-key").click();
  await expect(page.getByText(/仅允许输入英文|English letters only/)).toBeVisible();
  await expect(page.getByTestId("issue-form").locator('input[name="kbUserLabel"]')).toHaveAttribute(
    "placeholder",
    "Daniel Foster",
  );
  const name = await uniqueEnglishName("Eee User");
  await fillKbUserLabel(page, name);
  await page.getByTestId("issue-form").locator('button[type="submit"]').click();
  await expect(page.getByTestId("key-issued")).toBeVisible();
  const plaintext = await page.getByTestId("api-key-plaintext").innerText();
  expect(plaintext.startsWith("kb_live_")).toBeTruthy();
  await expect(page.getByTestId("api-key-plaintext")).toHaveCSS("white-space", "nowrap");
});

test("should_reveal_wechat_qr_when_hovering_contact_admin", async ({ page }) => {
  await page.goto("/login");
  const trigger = page.getByTestId("contact-admin");
  const qr = page.getByTestId("contact-admin-qr");
  await expect(trigger).toBeVisible();
  await expect(qr).toBeHidden();
  await trigger.hover();
  await expect(qr).toBeVisible();
  await expect(qr.locator("img")).toHaveAttribute("src", /EthanWeChat\.png/);
});

test("should_switch_locale_to_en", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("locale-en").click();
  await expect(page.getByTestId("admin-login")).toHaveText("Admin login");
  await page.getByTestId("locale-zh").click();
  await expect(page.getByTestId("admin-login")).toHaveText("管理员登录");
});

test("should_revoke_and_reissue_key", async ({ page }) => {
  await loginAndUnlock(page);
  const name = await uniqueEnglishName("Revoke User");
  await page.getByTestId("issue-key").click();
  await fillKbUserLabel(page, name);
  await page.getByTestId("issue-form").locator('button[type="submit"]').click();
  await expect(page.getByTestId("key-issued")).toBeVisible();
  await page.getByRole("button", { name: /返回列表|Back to list/ }).click();

  const row = page.locator("tbody tr").filter({ hasText: name }).filter({ hasText: /active/i }).first();
  await expect(row).toBeVisible();
  await expect(page.locator("tbody tr").filter({ hasText: name })).toHaveCount(1);
  await row.getByRole("button", { name: /重签|Reissue/ }).click();
  await expect(page.getByTestId("key-issued")).toBeVisible();
  const reissued = await page.getByTestId("api-key-plaintext").innerText();
  expect(reissued.startsWith("kb_live_")).toBeTruthy();
  await expect(page.getByTestId("api-key-plaintext")).toHaveCSS("white-space", "nowrap");
  await page.getByRole("button", { name: /返回列表|Back to list/ }).click();

  const row2 = page.locator("tbody tr").filter({ hasText: name }).filter({ hasText: /active/i });
  await row2.getByRole("button", { name: /吊销|Revoke/ }).click();
  await expect(page.getByTestId("confirm-dialog")).toBeVisible();
  await page.getByTestId("confirm-dialog-ok").click();
  await expect(page.locator("tbody tr").filter({ hasText: name })).toHaveCount(0);
});

test("should_toggle_password_visibility_on_login", async ({ page }) => {
  await page.goto("/login");
  const input = page.getByTestId("login-form").locator('input[name="password"]');
  await expect(input).toHaveAttribute("type", "password");
  await page.getByTestId("password-toggle-password").click();
  await expect(input).toHaveAttribute("type", "text");
});
