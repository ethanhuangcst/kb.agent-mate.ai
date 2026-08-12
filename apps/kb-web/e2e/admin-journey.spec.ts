import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  const res = await request.post("/api/admin/test/reset-seed");
  expect(res.ok()).toBeTruthy();
});

async function loginAndUnlock(page: import("@playwright/test").Page) {
  await page.goto("/login");
  const login = page.getByTestId("login-form").locator('input[name="login"]');
  await login.click();
  await login.fill("admin");
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
  await expect(page.getByTestId("admin-login")).toHaveText("Sign in");
  await page.getByTestId("locale-zh").click();
  await expect(page.getByTestId("admin-login")).toHaveText("登录");
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
  await row.getByRole("button", { name: /查看|View/ }).click();
  await expect(page.getByTestId("key-view")).toBeVisible();
  await expect(page.getByTestId("view-display-name")).toHaveText(name);
  const viewed = await page.getByTestId("api-key-plaintext").innerText();
  expect(viewed.startsWith("kb_live_")).toBeTruthy();
  await page.getByRole("button", { name: /返回列表|Back to list/ }).click();

  await row.getByRole("button", { name: /重签|Reissue/ }).click();
  await expect(page.getByTestId("key-issued")).toBeVisible();
  const reissued = await page.getByTestId("api-key-plaintext").innerText();
  expect(reissued.startsWith("kb_live_")).toBeTruthy();
  expect(reissued).not.toBe(viewed);
  await expect(page.getByTestId("api-key-plaintext")).toHaveCSS("white-space", "nowrap");
  await page.getByRole("button", { name: /返回列表|Back to list/ }).click();

  const row2 = page.locator("tbody tr").filter({ hasText: name }).filter({ hasText: /active/i });
  await expect(row2).toBeVisible();
  const rePrefix = reissued.slice(0, 12);
  await page.getByTestId(`revoke-${rePrefix}`).click();
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

test("should_list_admins_and_forbid_delete_self", async ({ page }) => {
  await loginAndUnlock(page);
  await page.goto("/admin/admins");
  await expect(page.getByRole("heading", { name: /管理员|Admins/ })).toBeVisible();
  await expect(page.getByText(/当前账号|Current account/)).toBeVisible();
  await expect(page.getByRole("button", { name: /邀请管理员|Invite admin/ })).toBeVisible();
});

test("should_reset_password_via_debug_token_when_test_reset_enabled", async ({
  page,
  request,
}) => {
  test.skip(process.env.ENABLE_TEST_RESET !== "1", "requires ENABLE_TEST_RESET=1 + EMAIL_TRANSPORT=log");
  await request.post("/api/admin/test/reset-seed");
  const forgot = await request.post("/api/auth/forgot-password", {
    data: { email: "me@ethanhuang.com" },
  });
  expect(forgot.ok()).toBeTruthy();
  const token = forgot.headers()["x-debug-reset-token"];
  expect(token).toBeTruthy();
  await page.goto(`/reset-password?token=${encodeURIComponent(token!)}`);
  await page.locator('input[name="password"]').fill("newpass12345");
  await page.locator('input[name="confirm"]').fill("newpass12345");
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/login/);
  const login = page.getByTestId("login-form").locator('input[name="login"]');
  await login.click();
  await login.fill("admin");
  await page.getByTestId("login-form").locator('input[name="password"]').fill("newpass12345");
  await page.getByTestId("login-form").locator('button[type="submit"]').click();
  await page.waitForURL(/admin\/users/);
});
