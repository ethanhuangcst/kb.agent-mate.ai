"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useTranslations } from "next-intl";

export function ForgotPasswordForm() {
  const t = useTranslations("forgot");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    const fd = new FormData(e.currentTarget);
    const email = String(fd.get("email") || "").trim();
    const res = await fetch("/api/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setPending(false);
    if (res.status === 503) {
      setError(t("mailUnavailable"));
      return;
    }
    if (res.status === 429) {
      setError(t("rateLimited"));
      return;
    }
    if (!res.ok) {
      setError(t("error"));
      return;
    }
    setDone(true);
  }

  if (done) {
    return (
      <div>
        <p className="lead">{t("sent")}</p>
        <Link className="btn-text" href="/login">
          {t("backLogin")}
        </Link>
      </div>
    );
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <label>
        {t("emailLabel")}
        <input type="email" name="email" placeholder="name@domain.com" required autoComplete="email" />
      </label>
      {error ? <p className="form-error">{error}</p> : null}
      <div className="form-actions btn-row">
        <button type="submit" className="btn" disabled={pending}>
          {t("submit")}
        </button>
        <Link className="btn-text" href="/login">
          {t("backLogin")}
        </Link>
      </div>
    </form>
  );
}
