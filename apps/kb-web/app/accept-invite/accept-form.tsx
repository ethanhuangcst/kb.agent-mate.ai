"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { isEnglishDisplayName } from "@/lib/display-name";
import { isValidUsername, normalizeUsername } from "@/lib/username";
import { NonContactTextInput } from "../non-contact-text-input";
import { PasswordField } from "../password-field";

export function AcceptInviteForm() {
  const t = useTranslations("acceptInvite");
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [email, setEmail] = useState<string | null>(null);
  const [tokenState, setTokenState] = useState<"loading" | "ok" | "bad">("loading");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!token) {
      setTokenState("bad");
      return;
    }
    void (async () => {
      const res = await fetch(`/api/auth/accept-invite?token=${encodeURIComponent(token)}`);
      if (!res.ok) {
        setTokenState("bad");
        return;
      }
      const data = await res.json();
      setEmail(data.email || null);
      setTokenState("ok");
    })();
  }, [token]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    const username = normalizeUsername(String(fd.get("username") || ""));
    const displayName = String(fd.get("displayName") || "");
    const password = String(fd.get("password") || "");
    const confirm = String(fd.get("confirm") || "");
    if (!isValidUsername(username)) {
      setError(t("usernameInvalid"));
      return;
    }
    if (!isEnglishDisplayName(displayName)) {
      setError(t("nameInvalid"));
      return;
    }
    if (password.length < 8) {
      setError(t("tooShort"));
      return;
    }
    if (password !== confirm) {
      setError(t("mismatch"));
      return;
    }
    setPending(true);
    const res = await fetch("/api/auth/accept-invite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token,
        username,
        displayName: displayName.trim(),
        password,
        confirm,
      }),
    });
    setPending(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (data.code === "USERNAME_INVALID") setError(t("usernameInvalid"));
      else if (data.code === "USERNAME_TAKEN") setError(t("usernameTaken"));
      else if (data.code === "NAME_INVALID") setError(t("nameInvalid"));
      else if (data.code === "INVALID_TOKEN" || data.code === "TOKEN_EXPIRED") setError(t("invalidToken"));
      else setError(t("error"));
      return;
    }
    router.push("/admin/users");
  }

  if (tokenState === "loading") {
    return <p className="lead">{t("checking")}</p>;
  }
  if (tokenState === "bad") {
    return (
      <div>
        <p className="lead">{t("invalidToken")}</p>
        <Link className="btn-text" href="/login">
          {t("backLogin")}
        </Link>
      </div>
    );
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      {email ? (
        <p className="lead">
          {t("emailLead")} <span className="mono">{email}</span>
        </p>
      ) : null}
      <label>
        {t("usernameLabel")}
        <NonContactTextInput
          name="username"
          placeholder="kbadmin"
          required
        />
      </label>
      <p className="hint">{t("usernameHint")}</p>
      <label>
        {t("nameLabel")}
        <NonContactTextInput name="displayName" placeholder="Alex Chen" required />
      </label>
      <p className="hint">{t("nameHint")}</p>
      <PasswordField name="password" label={t("newPassword")} autoComplete="new-password" />
      <PasswordField name="confirm" label={t("confirmPassword")} autoComplete="new-password" />
      {error ? <p className="form-error">{error}</p> : null}
      <div className="form-actions btn-row">
        <button type="submit" className="btn" disabled={pending}>
          {t("submit")}
        </button>
      </div>
    </form>
  );
}
