import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const LOCALES = new Set(["zh-CN", "en"]);

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const locale = String(body.locale || "");
  if (!LOCALES.has(locale)) {
    return NextResponse.json({ code: "INVALID_LOCALE" }, { status: 400 });
  }
  const jar = await cookies();
  jar.set("NEXT_LOCALE", locale, {
    path: "/",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 365,
  });
  return NextResponse.json({ locale });
}
