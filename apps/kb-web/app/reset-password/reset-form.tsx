"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { PasswordField } from "../password-field";

export function ResetPasswordForm() {
  const t = useTranslations("reset");
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [tokenState, setTokenState] = useState<"loading" | "ok" | "bad">("loading");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!token) {
      setTokenState("bad");
      return;
    }
    void (async () => {
      const res = await fetch(`/api/auth/reset-password?token=${encodeURIComponent(token)}`);
      setTokenState(res.ok ? "ok" : "bad");
    })();
  }, [token]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    const password = String(fd.get("password") || "");
    const confirm = String(fd.get("confirm") || "");
    if (password !== confirm) {
      setError(t("mismatch"));
      return;
    }
    if (password.length < 8) {
      setError(t("tooShort"));
      return;
    }
    setPending(true);
    const res = await fetch("/api/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, password, confirm }),
    });
    setPending(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (data.code === "TOKEN_EXPIRED" || data.code === "INVALID_TOKEN") {
        setError(t("invalidToken"));
      } else if (data.code === "PASSWORD_TOO_SHORT") {
        setError(t("tooShort"));
      } else {
        setError(t("error"));
      }
      return;
    }
    router.push("/login");
  }

  if (tokenState === "loading") {
    return <p className="lead">{t("checking")}</p>;
  }
  if (tokenState === "bad") {
    return (
      <div>
        <p className="lead">{t("invalidToken")}</p>
        <Link className="btn-text" href="/forgot-password">
          {t("requestAgain")}
        </Link>
      </div>
    );
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <PasswordField name="password" label={t("newPassword")} autoComplete="new-password" />
      <PasswordField name="confirm" label={t("confirmPassword")} autoComplete="new-password" />
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
