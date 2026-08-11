"use client";

export function LogoutLink({ label }: { label: string }) {
  return (
    <a
      href="/login"
      data-testid="logout"
      onClick={(e) => {
        e.preventDefault();
        void fetch("/api/auth/logout", { method: "POST" }).then(() => {
          window.location.href = "/login";
        });
      }}
    >
      {label}
    </a>
  );
}
