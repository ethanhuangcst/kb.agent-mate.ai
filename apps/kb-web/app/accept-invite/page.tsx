import Link from "next/link";
import { Suspense } from "react";
import { getTranslations } from "next-intl/server";
import { BrandLockup, ShellLocale, SiteFooter } from "../site-chrome";
import { AcceptInviteForm } from "./accept-form";

export default async function AcceptInvitePage() {
  const t = await getTranslations("acceptInvite");

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
            <AcceptInviteForm />
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
