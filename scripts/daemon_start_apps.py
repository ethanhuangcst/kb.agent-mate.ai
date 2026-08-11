#!/usr/bin/env python3
"""Double-fork local kb apps so they outlive Cursor agent-exec shells.

Root cause of frequent stops: uvicorn/next were children of
`Cursor Helper … agent-exec`. When the agent aborts a background shell
(or the tool session ends), those children receive shutdown and exit cleanly
— looking like “services keep dying”.

Usage (from repo root):
  .venv/bin/python scripts/daemon_start_apps.py
  # or: make up-daemon
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIDS = ROOT / ".pids"
VENV_UVICORN = ROOT / ".venv" / "bin" / "uvicorn"
ENV_FILE = ROOT / ".env"


def _load_dotenv(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not path.is_file():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _read_pid(name: str) -> int | None:
    p = PIDS / f"{name}.pid"
    if not p.is_file():
        return None
    try:
        return int(p.read_text().strip())
    except ValueError:
        return None


def _alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_pattern(pattern: str) -> None:
    subprocess.run(["pkill", "-f", pattern], check=False, capture_output=True)


def stop_all() -> None:
    for name in ("kb-agent", "kb-rag", "kb-web"):
        pid = _read_pid(name)
        if _alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)  # type: ignore[arg-type]
            except OSError:
                pass
        pid_file = PIDS / f"{name}.pid"
        if pid_file.exists():
            pid_file.unlink(missing_ok=True)
    _stop_pattern("uvicorn app.main:app")
    _stop_pattern("next dev")
    time.sleep(0.5)


def _daemonize_and_exec(name: str, cwd: Path, argv: list[str], env: dict[str, str]) -> int:
    """Classic double-fork; grandchild execs and is reparented away from agent-exec."""
    PIDS.mkdir(parents=True, exist_ok=True)
    log_path = PIDS / f"{name}.log"
    pid_path = PIDS / f"{name}.pid"

    # First fork
    pid = os.fork()
    if pid > 0:
        # Parent waits briefly for pid file
        for _ in range(50):
            if pid_path.is_file():
                break
            time.sleep(0.05)
        try:
            return int(pid_path.read_text().strip())
        except Exception:
            return pid

    # Intermediate child
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)

    # Grandchild — durable process
    os.chdir(cwd)
    os.umask(0)
    with open(log_path, "a", encoding="utf-8") as log:
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.close(devnull)

    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    os.execvpe(argv[0], argv, env)


def start_all() -> None:
    if not VENV_UVICORN.is_file():
        print("Missing venv uvicorn — run: make install-py", file=sys.stderr)
        sys.exit(1)
    env = _load_dotenv(ENV_FILE)
    stop_all()

    rag_pid = _daemonize_and_exec(
        "kb-rag",
        ROOT / "services" / "kb-rag",
        [str(VENV_UVICORN), "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
        env,
    )
    agent_pid = _daemonize_and_exec(
        "kb-agent",
        ROOT / "services" / "kb-agent",
        [str(VENV_UVICORN), "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env,
    )
    web_env = env.copy()
    web_pid = _daemonize_and_exec(
        "kb-web",
        ROOT / "apps" / "kb-web",
        ["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000"],
        web_env,
    )

    time.sleep(2)
    print(f"kb-rag   pid={rag_pid}  :8001  log={PIDS}/kb-rag.log")
    print(f"kb-agent pid={agent_pid}  :8000  log={PIDS}/kb-agent.log")
    print(f"kb-web   pid={web_pid}  :3000  log={PIDS}/kb-web.log")
    print("Detached from agent shell (double-fork). Parent should be launchd/init, not Cursor agent-exec.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in {"stop", "down"}:
        stop_all()
        print("Stopped kb-rag / kb-agent / kb-web")
        return
    start_all()


if __name__ == "__main__":
    main()
