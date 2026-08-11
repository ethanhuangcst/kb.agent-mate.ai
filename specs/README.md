# Specs index — kb.agent-mate.ai

Product and engineering specs for the private knowledge-base agent.

## Product & backlog

| Doc | Role |
| --- | --- |
| [req.md](./req.md) | Product requirements |
| [story-mapping.md](./story-mapping.md) | Backlog（Web / Agent / **MCP** / RAG）、MVP batches、Gherkin AC |
| [mvp-2-3-delivery.md](./mvp-2-3-delivery.md) | Closed-loop DoD (no fake stack for Done) |

## Design

| Doc | Role |
| --- | --- |
| [architecture.md](./architecture.md) | System architecture, REST table, tech stack |
| [agent-design.md](./agent-design.md) | Tool semantics, policy codes, host-model boundary |
| [mcp-design.md](./mcp-design.md) | MCP transport (`/mcp`), auth, tools, Cursor；故事 `mcp-01`…`06` |
| [rag-design.md](./rag-design.md) | Index / retrieve pipeline |
| [web-ui-design.md](./web-ui-design.md) | Admin UI |
| [test-strategy.md](./test-strategy.md) | Project test strategy (extends common-test-strategy) |

## Ops & keys

| Doc | Role |
| --- | --- |
| [keys.md](./keys.md) | Env var catalog (no secrets) |
| [deployment-plan.md](./deployment-plan.md) | Portainer / NPM / GHCR |
| [release-bot-instruction.md](./release-bot-instruction.md) | Release-bot consumer notes |

## Decisions & knowledge

| Path | Role |
| --- | --- |
| [adr/](./adr/) | Architecture Decision Records |
| [knowledge/](./knowledge/) | Reusable ops / frontend / design notes |

## Machine contracts

See [`../contracts/`](../contracts/) (`mcp-tools.json`, search response schema).
