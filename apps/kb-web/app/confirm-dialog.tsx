"use client";

import { useEffect, useId, useRef } from "react";
import { useTranslations } from "next-intl";

type Props = {
  open: boolean;
  title: string;
  body: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Zero-radius confirm dialog matching admin shell. */
export function ConfirmDialog({ open, title, body, confirmLabel, onConfirm, onCancel }: Props) {
  const t = useTranslations("common");
  const titleId = useId();
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    cancelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="dialog-backdrop" role="presentation" onClick={onCancel}>
      <div
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        data-testid="confirm-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} className="dialog-title">
          {title}
        </h2>
        <p className="dialog-body">{body}</p>
        <div className="dialog-actions">
          <button
            type="button"
            className="btn btn-danger"
            data-testid="confirm-dialog-ok"
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
          <button
            ref={cancelRef}
            type="button"
            className="btn btn-ghost"
            data-testid="confirm-dialog-cancel"
            onClick={onCancel}
          >
            {t("cancel")}
          </button>
        </div>
      </div>
    </div>
  );
}
