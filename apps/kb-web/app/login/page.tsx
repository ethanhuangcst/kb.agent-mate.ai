import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { BrandLockup, SiteFooter } from "../site-chrome";
import { LoginForm } from "./login-form";
import { LoginLead } from "./login-lead";

export default async function LoginPage() {
  const t = await getTranslations("login");

  return (
    <div className="auth-shell">
      <main className="auth-main">
        <div className="auth-card">
          <BrandLockup size="auth" />
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <LoginLead />
          <hr className="rule" />
          <LoginForm />
          <Link className="back-link" href="/">
            {t("backHome")}
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
