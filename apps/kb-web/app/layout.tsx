import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { Outfit, Noto_Sans_SC, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import "./admin-ui.css";
import { ensureSeedAdmin } from "@/lib/seed";

const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const noto = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-noto",
});
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono-g" });

export const metadata: Metadata = {
  title: "kb.agent-mate.ai",
  description: "Private knowledge-base agent",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  await ensureSeedAdmin().catch(() => undefined);
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body className={`${outfit.variable} ${noto.variable} ${mono.variable}`}>
        <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
