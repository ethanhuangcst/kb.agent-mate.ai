import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { LocaleSwitcher } from "./locale-switcher";

/** Site footer matching mockup: copyright inside each shell. */
export async function SiteFooter({ withLocale = true }: { withLocale?: boolean }) {
  const t = await getTranslations();
  return (
    <footer className="site-footer">
      {withLocale ? <LocaleSwitcher /> : null}
      <p>{t("footerCopyright")}</p>
    </footer>
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
