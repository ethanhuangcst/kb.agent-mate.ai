"use client";

import { useTranslations } from "next-intl";

/** Login lead: hover/focus “联系管理员” reveals WeChat QR (冷淡浮层). */
export function LoginLead() {
  const t = useTranslations("login");

  return (
    <p className="lead">
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
      })}
    </p>
  );
}
