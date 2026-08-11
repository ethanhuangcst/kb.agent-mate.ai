"use client";

import { useTranslations } from "next-intl";

/** Closed-registration notice plate; hover/focus “联系管理员” shows WeChat QR. */
export function LoginLead() {
  const t = useTranslations("login");

  return (
    <p className="auth-status" role="status" data-testid="login-status">
      {t.rich("lead", {
        contact: (chunks) => (
          <span className="contact-admin">
            <button
              type="button"
              className="contact-admin-trigger"
              aria-describedby="login-wechat-qr"
              data-testid="contact-admin"
            >
              {chunks}
            </button>
            <span
              id="login-wechat-qr"
              className="contact-admin-pop"
              role="tooltip"
              data-testid="contact-admin-qr"
            >
              <img
                src="/EthanWeChat.png"
                alt={t("wechatQrAlt")}
                width={180}
                height={180}
              />
              <span className="contact-admin-caption">{t("wechatQrCaption")}</span>
            </span>
          </span>
        ),
        key: (chunks) => <code className="auth-status-key">{chunks}</code>,
      })}
    </p>
  );
}
