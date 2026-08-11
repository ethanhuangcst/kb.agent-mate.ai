# kb-schema

Shared SQLAlchemy 2 models and Alembic migrations for **kb.agent-mate.ai**.

## Install (editable)

From a service directory:

```bash
pip install -e ../../packages/kb_schema
```

## Environment

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | SQLAlchemy URL (Postgres for product path; e.g. `postgresql+psycopg://…`) |

Local Compose often maps Postgres to **`127.0.0.1:5434`** (see `specs/keys.md`, `specs/knowledge/ops/local-postgres-5434.md`). Prefer **`make up-daemon`** from repo root (runs migrate + durable apps).

## Migrate

From repo root (preferred; also invoked by `make up-daemon`):

```bash
make migrate
```

Or:

```bash
export DATABASE_URL=postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent
cd packages/kb_schema
alembic upgrade head
```

## Seed admin

```python
from kb_schema import get_session, ensure_seed_admin

Session = get_session()
with Session() as session:
    ensure_seed_admin(session)
```

If no `admin_users` rows exist, creates `username=admin` / `password=admin` with `must_change_password=True`.

## Exports

`Base`, models (`AdminUser`, `User`, `ApiKey`, `KnowledgeItem`, …), `get_engine`, `get_session`, `ensure_seed_admin`.
