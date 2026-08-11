"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { ConfirmDialog } from "../../confirm-dialog";
import { NonContactTextInput } from "../../non-contact-text-input";
import { isEnglishDisplayName } from "@/lib/display-name";

type UserRow = {
  id: string;
  key_id: string;
  display_name: string;
  key_prefix: string;
  status: string;
  created_at: string;
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toISOString().slice(0, 10);
}

export function UsersPanel() {
  const t = useTranslations("admin");
  const [users, setUsers] = useState<UserRow[]>([]);
  const [issuedKey, setIssuedKey] = useState<string | null>(null);
  const [showIssue, setShowIssue] = useState(false);
  const [copied, setCopied] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<UserRow | null>(null);

  const load = useCallback(async () => {
    const res = await fetch("/api/admin/users");
    if (!res.ok) return;
    const data = await res.json();
    setUsers(data.users || []);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onIssue(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setNameError(null);
    const fd = new FormData(e.currentTarget);
    const displayName = String(fd.get("kbUserLabel") || "");
    if (!isEnglishDisplayName(displayName)) {
      setNameError(t("nameInvalid"));
      return;
    }
    const res = await fetch("/api/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ displayName: displayName.trim() }),
    });
    if (!res.ok) {
      if (res.status === 400) setNameError(t("nameInvalid"));
      return;
    }
    const data = await res.json();
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
    // Let WebKit dismiss Contact AutoFill before swapping to the issued view
    await new Promise((r) => window.setTimeout(r, 80));
    setShowIssue(false);
    setIssuedKey(data.apiKey);
    setCopied(false);
    await load();
  }

  async function confirmRevoke() {
    if (!revokeTarget) return;
    const id = revokeTarget.key_id;
    setRevokeTarget(null);
    await fetch(`/api/admin/keys/${id}/revoke`, { method: "POST" });
    await load();
  }

  async function reissue(id: string) {
    const res = await fetch(`/api/admin/keys/${id}/reissue`, { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    setIssuedKey(data.apiKey);
    setCopied(false);
    await load();
  }

  async function copyKey() {
    if (!issuedKey) return;
    try {
      await navigator.clipboard.writeText(issuedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* ignore */
    }
  }

  if (issuedKey) {
    return (
      <div data-testid="key-issued">
        <div className="page-head">
          <div>
            <p className="eyebrow">{t("issuedEyebrow")}</p>
            <h1>{t("issuedTitle")}</h1>
            <p>{t("issuedWarn")}</p>
          </div>
        </div>
        <div className="key-panel">
          <div className="code-block">
            <button
              type="button"
              className={`btn-copy${copied ? " is-copied" : ""}`}
              onClick={() => void copyKey()}
              aria-label={t("copy")}
              title={t("copy")}
            >
              <svg className="icon-copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
                <rect x="9" y="9" width="11" height="11" rx="0" />
                <path d="M5 15V5h10" />
              </svg>
              <svg className="icon-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
                <path d="M5 12.5l4.5 4.5L19 7" />
              </svg>
            </button>
            <pre>
              <code data-testid="api-key-plaintext">{issuedKey}</code>
            </pre>
          </div>
          <p className="warn">{t("issuedWarnStrong")}</p>
        </div>
        <div className="btn-row" style={{ marginTop: "2rem" }}>
          <button type="button" className="btn btn-ghost" onClick={() => setIssuedKey(null)}>
            {t("backList")}
          </button>
        </div>
      </div>
    );
  }

  if (showIssue) {
    return (
      <div data-testid="issue-panel">
        <div className="page-head">
          <div>
            <p className="eyebrow">{t("issueEyebrow")}</p>
            <h1>{t("issueTitle")}</h1>
            <p>{t("issueLead")}</p>
          </div>
        </div>
        <form
          className="form"
          onSubmit={onIssue}
          data-testid="issue-form"
          style={{ maxWidth: 420 }}
          autoComplete="off"
        >
          <div className="field">
            <span className="field-label">{t("userName")}</span>
            <p className="field-note">{t("nameEnglishOnly")}</p>
            <NonContactTextInput
              name="kbUserLabel"
              required
              aria-label={t("nameEnglishOnly")}
              placeholder={t("namePlaceholder")}
              pattern="[A-Za-z]+([ .'\-][A-Za-z]+)*"
              title={t("nameEnglishOnly")}
            />
          </div>
          {nameError ? (
            <p className="error" role="alert">
              {nameError}
            </p>
          ) : null}
          <p className="hint">{t("issueHint")}</p>
          <div className="form-actions btn-row">
            <button type="submit" className="btn">
              {t("issueSubmit")}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowIssue(false)}>
              {t("cancel")}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <p className="eyebrow">{t("usersEyebrow")}</p>
          <h1>{t("usersTitle")}</h1>
          <p>{t("usersLead")}</p>
        </div>
        <button
          type="button"
          className="btn btn-page"
          data-testid="issue-key"
          onClick={() => setShowIssue(true)}
        >
          {t("issueKey")}
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t("displayName")}</th>
              <th>{t("keyPrefix")}</th>
              <th>{t("status")}</th>
              <th>{t("issuedAt")}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={5}>{t("empty")}</td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.key_id} data-testid={`user-row-${u.key_prefix}`}>
                  <td>{u.display_name}</td>
                  <td className="mono">{u.key_prefix}</td>
                  <td>
                    <span className="status is-on">{t("active")}</span>
                  </td>
                  <td className="mono">{formatDate(u.created_at)}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-text" onClick={() => void reissue(u.key_id)}>
                        {t("reissue")}
                      </button>
                      <button
                        type="button"
                        className="btn-text btn-danger-text"
                        data-testid={`revoke-${u.key_prefix}`}
                        onClick={() => setRevokeTarget(u)}
                      >
                        {t("revoke")}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={Boolean(revokeTarget)}
        title={t("revokeConfirmTitle")}
        body={t("revokeConfirmBody")}
        confirmLabel={t("revokeConfirmAction")}
        onConfirm={() => void confirmRevoke()}
        onCancel={() => setRevokeTarget(null)}
      />
    </div>
  );
}
