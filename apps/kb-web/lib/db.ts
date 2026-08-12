import postgres from "postgres";

function databaseUrl(): string {
  const raw =
    process.env.DATABASE_URL ||
    "postgresql://kb:kb_dev_password@127.0.0.1:5434/kb_agent";
  return raw.replace("postgresql+psycopg://", "postgresql://");
}

const globalForDb = globalThis as unknown as { __kbSql?: ReturnType<typeof postgres> };

export const sql =
  globalForDb.__kbSql ??
  postgres(databaseUrl(), {
    max: 10,
    prepare: false,
  });

if (process.env.NODE_ENV !== "production") {
  globalForDb.__kbSql = sql;
}
