import { clearedSessionResponse } from "@/lib/session";

export async function POST() {
  return clearedSessionResponse({ ok: true });
}
