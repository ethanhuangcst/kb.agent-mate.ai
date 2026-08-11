import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import "./globals.css";
import "./admin-ui.css";
import { ensureSeedAdmin } from "@/lib/seed";

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
      <body>
        <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
