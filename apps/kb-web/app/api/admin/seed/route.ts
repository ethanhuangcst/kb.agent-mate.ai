import { NextResponse } from "next/server";
import { ensureSeedAdmin } from "@/lib/seed";

export async function POST() {
  const result = await ensureSeedAdmin();
  return NextResponse.json(result);
}
