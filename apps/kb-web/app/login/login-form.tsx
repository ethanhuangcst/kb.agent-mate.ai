"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { NonContactTextInput } from "../non-contact-text-input";
import { PasswordField } from "../password-field";

export function LoginForm() {
  const t = useTranslations("login");
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    const fd = new FormData(e.currentTarget);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        login: fd.get("login"),
        password: fd.get("password"),
      }),
    });
    setPending(false);
    if (!res.ok) {
      setError(t("error"));
      return;
    }
    const data = await res.json();
    router.push(data.mustChangePassword ? "/change-password" : "/admin/users");
    router.refresh();
  }

  return (
    <form className="form" onSubmit={onSubmit} data-testid="login-form" autoComplete="off">
      <label>
        {t("loginLabel")}
        <NonContactTextInput name="login" placeholder="admin" required />
      </label>
      <PasswordField name="password" label={t("passwordLabel")} autoComplete="current-password" />
      {error ? (
        <p className="error" role="alert" data-testid="login-error">
          {error}
        </p>
      ) : null}
      <div className="form-actions btn-row">
        <button type="submit" className="btn" disabled={pending}>
          {t("submit")}
        </button>
        <Link className="btn-text" href="/forgot-password">
          {t("forgot")}
        </Link>
      </div>
    </form>
  );
}
