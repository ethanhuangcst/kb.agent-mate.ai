# kb-schema

Shared SQLAlchemy 2 models and Alembic migrations for **kb.agent-mate.ai** (MVP-1).

## Install (editable)

From a service directory:

```bash
pip install -e ../../packages/kb_schema
```

## Environment

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | SQLAlchemy URL (e.g. `postgresql+psycopg://…` or `sqlite+pysqlite:///…` for tests) |

## Migrate

```bash
export DATABASE_URL=postgresql+psycopg://kb:kb@localhost:5432/kb
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

`Base`, models (`AdminUser`, `User`, `ApiKey`, `KnowledgeItem`), `get_engine`, `get_session`, `ensure_seed_admin`.
