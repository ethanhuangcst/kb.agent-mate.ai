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
    <div
      className="locale-switch"
      role="group"
      aria-label={t("label")}
      data-testid="locale-switcher"
    >
      <button
        type="button"
        className={locale === "zh-CN" ? "is-active" : undefined}
        aria-pressed={locale === "zh-CN"}
        data-testid="locale-zh"
        onClick={() => setLocale("zh-CN")}
      >
        {t("zh")}
      </button>
      <button
        type="button"
        className={locale === "en" ? "is-active" : undefined}
        aria-pressed={locale === "en"}
        data-testid="locale-en"
        onClick={() => setLocale("en")}
      >
        {t("en")}
      </button>
    </div>
  );
}
