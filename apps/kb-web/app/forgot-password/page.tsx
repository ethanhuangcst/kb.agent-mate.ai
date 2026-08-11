import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { BrandLockup, SiteFooter } from "../site-chrome";

/** Visual stub — forgot-password story is MVP-3; UI matches mockup. */
export default async function ForgotPasswordPage() {
  const t = await getTranslations("forgot");

  return (
    <div className="auth-shell">
      <main className="auth-main">
        <div className="auth-card">
          <BrandLockup size="auth" />
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p className="lead">{t("lead")}</p>
          <hr className="rule" />
          <form className="form" action="/login">
            <label>
              {t("emailLabel")}
              <input type="email" name="email" placeholder="name@domain.com" />
            </label>
            <div className="form-actions btn-row">
              <button type="submit" className="btn">
                {t("submit")}
              </button>
              <Link className="btn-text" href="/login">
                {t("backLogin")}
              </Link>
            </div>
          </form>
          <Link className="back-link" href="/">
            {t("backHome")}
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
