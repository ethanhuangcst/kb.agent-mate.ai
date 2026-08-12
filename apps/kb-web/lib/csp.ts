export type CspOptions = {
  isDev?: boolean;
};

/**
 * Build a strict CSP that blocks un-nonced inline / data: scripts (ClickFix loaders)
 * while allowing Next.js hydration via nonce + strict-dynamic.
 */
export function buildContentSecurityPolicy(nonce: string, options: CspOptions = {}): string {
  const isDev = options.isDev === true;
  const scriptSrc = [
    "'self'",
    `'nonce-${nonce}'`,
    "'strict-dynamic'",
    ...(isDev ? ["'unsafe-eval'"] : []),
  ].join(" ");

  const directives = [
    "default-src 'self'",
    `script-src ${scriptSrc}`,
    // Styles: keep unsafe-inline for React style attrs / CSS-in-JS; scripts stay strict.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    isDev ? "connect-src 'self' ws: wss:" : "connect-src 'self'",
  ];

  if (!isDev) {
    directives.push("upgrade-insecure-requests");
  }

  return directives.join("; ");
}
