import Link from "next/link";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { getSession } from "@/lib/session";
import { BrandLockup, SiteFooter } from "../site-chrome";
import { ChangePasswordForm } from "./change-password-form";

export default async function ChangePasswordPage() {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!session.mustChangePassword) redirect("/admin/users");

  const t = await getTranslations("changePassword");

  return (
    <div className="auth-shell">
      <main className="auth-main">
        <div className="auth-card">
          <BrandLockup size="auth" />
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p className="lead">{t("lead")}</p>
          <hr className="rule" />
          <ChangePasswordForm />
          <Link className="back-link" href="/login">
            {t("backLogin")}
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
