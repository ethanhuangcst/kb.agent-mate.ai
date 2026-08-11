import { getTranslations } from "next-intl/server";

export default async function AdminsPage() {
  const t = await getTranslations("admin");
  return (
    <div>
      <div className="page-head">
        <div>
          <p className="eyebrow">Admins</p>
          <h1>{t("admins")}</h1>
          <p>{t("adminsSoon")}</p>
        </div>
      </div>
    </div>
  );
}
