import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { BrandLockup, ShellLocale, SiteFooter } from "./site-chrome";

export default async function HomePage() {
  const t = await getTranslations("home");

  return (
    <div className="home-shell">
      <ShellLocale />
      <main className="home-main">
        <div className="home-card">
          <BrandLockup size="home" />
          <p className="tagline">{t("tagline")}</p>
          <div className="home-actions">
            <Link className="home-link" href="/guide">
              {t("guide")}
            </Link>
            <Link className="btn btn-page" href="/login" data-testid="admin-login">
              {t("adminLogin")}
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
