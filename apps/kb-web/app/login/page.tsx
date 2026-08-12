import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { BrandLockup, ShellLocale, SiteFooter } from "../site-chrome";
import { LoginForm } from "./login-form";
import { LoginLead } from "./login-lead";

export default async function LoginPage() {
  const t = await getTranslations("login");

  return (
    <div className="auth-shell">
      <ShellLocale />
      <main className="auth-main">
        <div className="auth-card auth-card-login">
          <BrandLockup size="auth" />
          <div className="auth-login-panel">
            <LoginLead />
            <div className="auth-work">
              <h1>{t("title")}</h1>
              <LoginForm />
              <Link className="back-link" href="/">
                {t("backHome")}
              </Link>
            </div>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
