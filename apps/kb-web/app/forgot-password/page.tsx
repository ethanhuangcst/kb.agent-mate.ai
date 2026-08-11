import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { BrandLockup, ShellLocale, SiteFooter } from "../site-chrome";
import { ForgotPasswordForm } from "./forgot-form";

export default async function ForgotPasswordPage() {
  const t = await getTranslations("forgot");

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
          <ForgotPasswordForm />
          <Link className="back-link" href="/">
            {t("backHome")}
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
