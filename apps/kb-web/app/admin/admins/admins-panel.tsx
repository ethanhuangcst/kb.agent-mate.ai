"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { ConfirmDialog } from "../../confirm-dialog";

type AdminRow = {
  id: string;
  username: string | null;
  email: string | null;
  display_name: string | null;
  status: string;
  created_at: string;
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toISOString().slice(0, 10);
}

export function AdminsPanel({ currentAdminId }: { currentAdminId: string }) {
  const t = useTranslations("admin");
  const [admins, setAdmins] = useState<AdminRow[]>([]);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AdminRow | null>(null);
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    const res = await fetch("/api/admin/admins");
    if (!res.ok) return;
    const data = await res.json();
    setAdmins(data.admins || []);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onInvite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setInviteError(null);
    setInviteMsg(null);
    setPending(true);
    const fd = new FormData(form);
    const email = String(fd.get("email") || "").trim();
    const res = await fetch("/api/admin/admins", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setPending(false);
    if (res.status === 503) {
      setInviteError(t("inviteMailUnavailable"));
      return;
    }
    if (res.status === 409) {
      setInviteError(t("inviteEmailTaken"));
      return;
    }
    if (!res.ok) {
      setInviteError(t("inviteFailed"));
      return;
    }
    setInviteMsg(t("inviteSent"));
    form.reset();
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    const id = deleteTarget.id;
    setDeleteTarget(null);
    await fetch(`/api/admin/admins/${id}`, { method: "DELETE" });
    await load();
  }

  if (showInvite) {
    return (
      <div>
        <div className="page-head">
          <div>
            <p className="eyebrow">Admins</p>
            <h1>{t("inviteTitle")}</h1>
            <p>{t("inviteLead")}</p>
          </div>
          <button type="button" className="btn-text" onClick={() => setShowInvite(false)}>
            {t("backList")}
          </button>
        </div>
        <form className="form" style={{ maxWidth: 420 }} onSubmit={onInvite}>
          <label>
            {t("inviteEmailLabel")}
            <input type="email" name="email" placeholder="colleague@domain.com" required />
          </label>
          {inviteError ? <p className="form-error">{inviteError}</p> : null}
          {inviteMsg ? <p className="lead">{inviteMsg}</p> : null}
          <div className="form-actions btn-row">
            <button type="submit" className="btn" disabled={pending}>
              {t("inviteSubmit")}
            </button>
            <button type="button" className="btn-text" onClick={() => setShowInvite(false)}>
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
          <p className="eyebrow">Admins</p>
          <h1>{t("admins")}</h1>
          <p>{t("adminsLead")}</p>
        </div>
        <button type="button" className="btn btn-page" onClick={() => setShowInvite(true)}>
          {t("inviteAdmin")}
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t("adminUsername")}</th>
              <th>{t("adminDisplayName")}</th>
              <th>{t("adminEmail")}</th>
              <th>{t("status")}</th>
              <th>{t("adminCreated")}</th>
              <th>{t("actions")}</th>
            </tr>
          </thead>
          <tbody>
            {admins.length === 0 ? (
              <tr>
                <td colSpan={6}>{t("adminsEmpty")}</td>
              </tr>
            ) : (
              admins.map((a) => {
                const isSelf = a.id === currentAdminId;
                return (
                  <tr key={a.id}>
                    <td className="mono">{a.username || "—"}</td>
                    <td>{a.display_name || "—"}</td>
                    <td>{a.email || "—"}</td>
                    <td>
                      <span className="status is-on">{t("active")}</span>
                    </td>
                    <td className="mono">{formatDate(a.created_at)}</td>
                    <td>
                      <div className="row-actions">
                        {isSelf ? (
                          <span className="btn-text" style={{ border: "none", cursor: "default", color: "var(--mute-soft)" }}>
                            {t("currentAccount")}
                          </span>
                        ) : (
                          <button
                            type="button"
                            className="btn-text btn-danger-text"
                            onClick={() => setDeleteTarget(a)}
                          >
                            {t("deleteAdmin")}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title={t("deleteConfirmTitle")}
        body={t("deleteConfirmBody")}
        confirmLabel={t("deleteConfirmAction")}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
