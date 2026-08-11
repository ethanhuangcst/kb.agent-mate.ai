# ADR-008: Durable local app start (`make up-daemon`)

## Status
Accepted

## Context
Local uvicorn/Next processes started under Cursor Agent (`agent-exec`) were reaped when the agent aborted background shells or restarted. Operators saw “services keep dying” even though health checks had passed. Plain `nohup` from a short agent Shell still sat in a process group that could be cleaned up.

## Decision
Prefer **`make up-daemon`** for the local full stack (Postgres + Qdrant + migrate + kb-agent + kb-rag + kb-web). Implementation: `scripts/daemon_start_apps.py` double-forks so app PPIDs become `1` (launchd), independent of the agent tree. Keep `make up` / foreground `make dev` for system Terminal use. `make down-apps` / `make down` stop the durable processes.

## Consequences
- Docs, test strategy, and root README recommend `up-daemon` when driving from Agent.
- Ops note: `specs/knowledge/ops/local-apps-keep-dying.md`.
- Does not change production deploy (Portainer / compose on VPS).

## Date
2026-08-11
