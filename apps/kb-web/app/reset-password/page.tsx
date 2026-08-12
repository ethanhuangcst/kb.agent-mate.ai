import Link from "next/link";
import { Suspense } from "react";
import { getTranslations } from "next-intl/server";
import { BrandLockup, ShellLocale, SiteFooter } from "../site-chrome";
import { ResetPasswordForm } from "./reset-form";

export default async function ResetPasswordPage() {
  const t = await getTranslations("reset");

  return (
    <div className="auth-shell">
      <ShellLocale />
      <main className="auth-main">
        <div className="auth-card">
          <BrandLockup size="auth" />
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p className="lead">{t("lead")}</p>
          <hr className="rule" />
          <Suspense fallback={<p className="lead">{t("checking")}</p>}>
            <ResetPasswordForm />
          </Suspense>
          <Link className="back-link" href="/">
            {t("backHome")}
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
