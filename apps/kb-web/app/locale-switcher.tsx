"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const t = useTranslations("locale");

  async function setLocale(next: string) {
    await fetch("/api/locale", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ locale: next }),
    });
    router.refresh();
  }

  return (
    <div className="locale-switch" data-testid="locale-switcher">
      <span className="sr-only">{t("label")}</span>
      <button
        type="button"
        className={locale === "zh-CN" ? "active" : undefined}
        data-testid="locale-zh"
        onClick={() => setLocale("zh-CN")}
      >
        中文
      </button>
      <button
        type="button"
        className={locale === "en" ? "active" : undefined}
        data-testid="locale-en"
        onClick={() => setLocale("en")}
      >
        EN
      </button>
    </div>
  );
}
