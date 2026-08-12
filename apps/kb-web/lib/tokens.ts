import { createHash, randomBytes } from "crypto";

export function hashToken(raw: string): string {
  return createHash("sha256").update(raw).digest("hex");
}

export function generateRawToken(): string {
  return randomBytes(32).toString("base64url");
}

function isLoopbackHost(hostname: string): boolean {
  const h = hostname.toLowerCase();
  return h === "127.0.0.1" || h === "localhost" || h === "::1" || h === "[::1]";
}

/**
 * Absolute origin for transactional email links (reset / invite).
 * Prefers PUBLIC_BASE_URL (server canonical) over NEXT_PUBLIC_APP_URL.
 * Rewrites 127.0.0.1 → localhost so Safari HTTPS-First does not open
 * https://127.0.0.1 (port dropped). Production must be public HTTPS.
 */
export function publicAppBaseUrl(): string {
  const raw = (
    process.env.PUBLIC_BASE_URL ||
    process.env.NEXT_PUBLIC_APP_URL ||
    ""
  )
    .trim()
    .replace(/\/$/, "");

  const isProd = process.env.NODE_ENV === "production";
  const candidate = raw || (isProd ? "https://kb.agent-mate.ai" : "http://localhost:3000");

  let url: URL;
  try {
    url = new URL(candidate);
  } catch {
    throw new Error(`Invalid PUBLIC_BASE_URL / NEXT_PUBLIC_APP_URL: ${candidate}`);
  }

  if (isProd) {
    if (isLoopbackHost(url.hostname)) {
      throw new Error(
        "PUBLIC_BASE_URL must be the public HTTPS origin in production (e.g. https://kb.agent-mate.ai), not loopback",
      );
    }
    if (url.protocol !== "https:") {
      throw new Error("PUBLIC_BASE_URL must use https in production");
    }
  }

  // Safari HTTPS-First upgrades http://127.0.0.1:PORT to https://127.0.0.1 (drops port).
  if (url.hostname === "127.0.0.1") {
    url.hostname = "localhost";
  }

  if (isLoopbackHost(url.hostname) && url.protocol === "http:" && !url.port) {
    url.port = "3000";
  }

  return url.origin;
}

export const RESET_TOKEN_TTL_MS = 60 * 60 * 1000;
export const INVITE_TOKEN_TTL_MS = 72 * 60 * 60 * 1000;
