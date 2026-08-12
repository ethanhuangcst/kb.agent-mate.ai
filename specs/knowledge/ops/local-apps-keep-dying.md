# Ops: why local apps keep stopping

## Symptom
kb-agent `:8000`, kb-rag `:8001`, and/or kb-web `:3000` die soon after start; Cursor shows background task **aborted** / **success** with process gone.

## Root cause (primary)

Processes were started as children of **Cursor Agent** (`Cursor Helper … agent-exec`).

Evidence: `ps` showed uvicorn PPID = agent-exec. When the agent:

- aborts a previous background shell (e.g. on a new “restart all services”), or
- ends/reaps the tool session that owns that shell,

those children get a clean shutdown (`Shutting down` / `Stopping reloader`) — not an app crash.

This is **process-tree lifecycle**, not Postgres/Qdrant flakiness and usually not OOM.

## Contributing causes

| Cause | Effect |
| --- | --- |
| Agent `pkill` / `make stop-apps` on every restart | Intentional kill before relaunch |
| `make up` / `nohup` inside a short agent Shell | Job may die when that tool invocation’s process group is cleaned up |
| `block_until_ms: 0` shells tracked by Cursor | Stay up until Cursor marks the task aborted |

## What to do

**Preferred (durable):**

```bash
make up-daemon
```

Uses `scripts/daemon_start_apps.py` (double-fork) so apps are **not** under agent-exec. Stop with `make down-apps` or `make down`.

**Also fine:** run `make up` / `npm run dev` in **Terminal.app / iTerm** (outside the Agent).

**Avoid:** relying on Agent-background uvicorn as the long-lived local stack.

## Check

```bash
# Parent should NOT be "Cursor Helper … agent-exec"
ps -o pid,ppid,command -p $(lsof -nP -iTCP:8000 -sTCP:LISTEN -t)
make status
```

## Links
- ADR: [`adr/ADR-008-durable-local-up-daemon.md`](../../adr/ADR-008-durable-local-up-daemon.md)
- Root: [`README.md`](../../../README.md)
