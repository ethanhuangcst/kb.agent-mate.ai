"use client";

import { useId, useState } from "react";
import { useTranslations } from "next-intl";

type Props = {
  name: string;
  label: string;
  autoComplete?: string;
  placeholder?: string;
  required?: boolean;
};

/** Password input with show/hide toggle (冷淡线框眼睛). */
export function PasswordField({
  name,
  label,
  autoComplete = "current-password",
  placeholder = "••••••••••••",
  required = true,
}: Props) {
  const t = useTranslations("common");
  const [visible, setVisible] = useState(false);
  const inputId = useId();

  return (
    <label htmlFor={inputId}>
      {label}
      <span className="password-field">
        <input
          id={inputId}
          name={name}
          type={visible ? "text" : "password"}
          autoComplete={autoComplete}
          placeholder={placeholder}
          required={required}
        />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? t("hidePassword") : t("showPassword")}
          aria-pressed={visible}
          data-testid={`password-toggle-${name}`}
        >
          {visible ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
              <path d="M3 3l18 18" />
              <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
              <path d="M9.9 5.1A9.8 9.8 0 0 1 12 5c5 0 9.3 3.1 11 7-0.5 1.2-1.2 2.3-2.1 3.3" />
              <path d="M6.1 6.1C4.2 7.4 2.7 9.1 1 12c1.7 3.9 6 7 11 7 1.5 0 2.9-.3 4.2-.8" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
              <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          )}
        </button>
      </span>
    </label>
  );
}
