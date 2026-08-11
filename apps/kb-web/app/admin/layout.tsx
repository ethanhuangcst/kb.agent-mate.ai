import Link from "next/link";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { getSession } from "@/lib/session";
import { BrandLockup, SiteFooter } from "../site-chrome";
import { LocaleSwitcher } from "../locale-switcher";
import { LogoutLink } from "./logout-link";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (session.mustChangePassword) redirect("/change-password");

  const t = await getTranslations("admin");
  const name = session.displayName || session.username || "Admin";

  return (
    <div className="app-shell">
      <header className="app-header">
        <BrandLockup size="header" href="/" />
        <div className="header-end">
          <p className="hello">
            Hello, <span className="hello-name">{name}</span>
          </p>
          <LocaleSwitcher />
        </div>
      </header>
      <div className="app-body">
        <aside className="sidebar">
          <nav className="nav" aria-label={t("navLabel")}>
            <Link className="active" href="/admin/users">
              {t("users")}
            </Link>
            <Link href="/admin/admins">{t("admins")}</Link>
            <LogoutLink label={t("logout")} />
          </nav>
        </aside>
        <div className="main">
          <div className="content">{children}</div>
        </div>
      </div>
      <SiteFooter />
    </div>
  );
}
