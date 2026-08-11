import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { LocaleSwitcher } from "./locale-switcher";

/** Site footer matching mockup: copyright only (locale lives in header). */
export async function SiteFooter() {
  const t = await getTranslations();
  return (
    <footer className="site-footer">
      <p>{t("footerCopyright")}</p>
    </footer>
  );
}

/** Top-right locale for shells without a full app header (home / auth). */
export function ShellLocale() {
  return (
    <div className="shell-locale">
      <LocaleSwitcher />
    </div>
  );
}

export async function BrandLockup({
  href = "/",
  size = "auth",
}: {
  href?: string;
  size?: "auth" | "home" | "header";
}) {
  const t = await getTranslations();
  const dims = size === "header" ? 36 : 56;
  const imgClass = size === "header" ? "logo-header-mark" : "logo-full";
  const wrapClass =
    size === "header" ? "logo" : size === "home" ? "logo logo-home" : "logo logo-auth";

  const inner = (
    <>
      {/* Plain img: next/image quantizes logo to 8-bit and washes yellow */}
      <img className={imgClass} src="/logo.png" alt="" width={dims} height={dims} />
      <span className="logo-word">{t("brand")}</span>
    </>
  );

  if (size === "home") {
    return (
      <div className={wrapClass} aria-label={t("brand")}>
        {inner}
      </div>
    );
  }

  return (
    <Link className={wrapClass} href={href} aria-label={t("brand")}>
      {inner}
    </Link>
  );
}
