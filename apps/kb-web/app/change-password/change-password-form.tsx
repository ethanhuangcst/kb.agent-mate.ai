"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { PasswordField } from "../password-field";

export function ChangePasswordForm() {
  const t = useTranslations("changePassword");
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    const password = String(fd.get("password") || "");
    const confirm = String(fd.get("confirm") || "");
    if (password.length < 8) {
      setError(t("tooShort"));
      return;
    }
    if (password !== confirm) {
      setError(t("mismatch"));
      return;
    }
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password, confirm }),
    });
    if (!res.ok) {
      setError(t("mismatch"));
      return;
    }
    router.push("/admin/users");
    router.refresh();
  }

  return (
    <form className="form" onSubmit={onSubmit} data-testid="change-password-form">
      <PasswordField
        name="password"
        label={t("newPassword")}
        autoComplete="new-password"
      />
      <PasswordField
        name="confirm"
        label={t("confirmPassword")}
        autoComplete="new-password"
      />
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      <div className="form-actions btn-row">
        <button type="submit" className="btn">
          {t("submit")}
        </button>
      </div>
    </form>
  );
}
