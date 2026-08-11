import { Resend } from "resend";
import { publicAppBaseUrl } from "./tokens";

export type MailKind = "password_reset" | "admin_invite";

export type SentMail = {
  kind: MailKind;
  to: string;
  subject: string;
  url: string;
};

/** Last emails in log transport — for ENABLE_TEST_RESET / unit tests. */
const logOutbox: SentMail[] = [];

export function drainLogOutbox(): SentMail[] {
  return logOutbox.splice(0, logOutbox.length);
}

function fromAddress(): string {
  return process.env.RESEND_FROM_EMAIL || "onboarding@resend.dev";
}

function useLogTransport(): boolean {
  if (process.env.EMAIL_TRANSPORT === "log") return true;
  if (process.env.EMAIL_TRANSPORT === "resend") return false;
  return !process.env.RESEND_API_KEY;
}

export class MailUnavailableError extends Error {
  constructor(message = "MAIL_UNAVAILABLE") {
    super(message);
    this.name = "MailUnavailableError";
  }
}

async function send(kind: MailKind, to: string, subject: string, html: string, url: string): Promise<void> {
  if (useLogTransport()) {
    logOutbox.push({ kind, to, subject, url });
    if (process.env.NODE_ENV !== "test") {
      console.info(`[email:log] ${kind} → ${to} ${url}`);
    }
    return;
  }
  const key = process.env.RESEND_API_KEY;
  if (!key) {
    throw new MailUnavailableError();
  }
  const resend = new Resend(key);
  const { error } = await resend.emails.send({
    from: fromAddress(),
    to,
    subject,
    html,
  });
  if (error) {
    throw new MailUnavailableError(error.message || "MAIL_UNAVAILABLE");
  }
}

export async function sendPasswordResetEmail(to: string, rawToken: string): Promise<string> {
  const url = `${publicAppBaseUrl()}/reset-password?token=${encodeURIComponent(rawToken)}`;
  await send(
    "password_reset",
    to,
    "Reset your kb.agent-mate.ai admin password",
    `<p>Reset your admin password:</p><p><a href="${url}">${url}</a></p><p>This link expires in 1 hour and can be used once.</p>`,
    url,
  );
  return url;
}

export async function sendAdminInviteEmail(to: string, rawToken: string): Promise<string> {
  const url = `${publicAppBaseUrl()}/accept-invite?token=${encodeURIComponent(rawToken)}`;
  await send(
    "admin_invite",
    to,
    "You are invited as a kb.agent-mate.ai admin",
    `<p>You were invited to administer kb.agent-mate.ai.</p><p><a href="${url}">Set your username, name, and password</a></p><p>This link expires in 72 hours and can be used once.</p>`,
    url,
  );
  return url;
}
