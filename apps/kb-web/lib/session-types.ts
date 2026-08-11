export type SessionPayload = {
  adminId: string;
  username: string | null;
  displayName: string | null;
  mustChangePassword: boolean;
};
