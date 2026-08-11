import { getSession } from "@/lib/session";
import { AdminsPanel } from "./admins-panel";

export default async function AdminsPage() {
  const session = await getSession();
  return <AdminsPanel currentAdminId={session?.adminId || ""} />;
}
