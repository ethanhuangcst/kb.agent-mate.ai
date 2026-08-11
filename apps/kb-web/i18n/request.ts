import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
  const jar = await cookies();
  const cookieLocale = jar.get("NEXT_LOCALE")?.value;
  const locale =
    cookieLocale === "en" || cookieLocale === "zh-CN"
      ? cookieLocale
      : process.env.NEXT_PUBLIC_DEFAULT_LOCALE || "zh-CN";
  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
