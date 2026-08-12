# ADR-015: External search via fixture or Tavily adapter

## Status
Accepted

## Context
`agent-source-01` needs outbound web candidates without auto-ingest. Hard-coding a single vendor or requiring a live key for all tests would block CI and local DoD.

## Decision
- Introduce a `SourceAdapter` protocol with `FixtureSourceAdapter` (deterministic) and `TavilyAdapter` (`TAVILY_API_KEY`).
- Selection: `KB_SOURCE_USE_FIXTURE=true` → fixture; else Tavily when key present; else `SOURCE_UNAVAILABLE` (no silent empty success).
- Expose only `kb_external_search` / `POST /api/v1/kb/sources/search` (not `kb_source_search`).

## Rationale
Matches architecture Source Router sketch while keeping MVP to one production adapter. Fixture preserves contract tests without paid/outbound dependency. Explicit `SOURCE_UNAVAILABLE` avoids false “no results” UX.

## Consequences
- Production must set `TAVILY_API_KEY` (or enable fixture deliberately).
- Exa / multi-source ranking remain future work.
- Quota (`KB_EXTERNAL_SEARCH_RPM`) applies before adapter calls.

## Date
2026-08-11
