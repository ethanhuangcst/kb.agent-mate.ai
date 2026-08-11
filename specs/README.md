# Specs index — kb.agent-mate.ai

Product and engineering specs for the private knowledge-base agent.

Quick start (ports + `make up-daemon`): [root README](../README.md).

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
| [mcp-design.md](./mcp-design.md) | MCP：Cursor `/mcp` 或 stdio `mcp.json`；ChatBox `/sse`；`/guide` §3–§4；故事 `mcp-01`… |
| [knowledge-summary.md](./knowledge-summary.md) | Content overview ≤400 字；`kb_knowledge_summary` 读/刷新 |
| [rag-design.md](./rag-design.md) | Index / retrieve pipeline |
| [web-ui-design.md](./web-ui-design.md) | Admin UI + 接入指南图文步骤 |
| [test-strategy.md](./test-strategy.md) | Project test strategy (extends common-test-strategy) |

## Ops & keys

| Doc | Role |
| --- | --- |
| [keys.md](./keys.md) | Env var catalog (no secrets) |
| [deployment-plan.md](./deployment-plan.md) | Portainer / NPM / GHCR；§7.1 MCP 客户端配置 |
| [knowledge/ops/local-apps-keep-dying.md](./knowledge/ops/local-apps-keep-dying.md) | 本地 app 被 Agent 回收 → `make up-daemon` |
| [release-bot-instruction.md](./release-bot-instruction.md) | Release-bot consumer notes |

## Decisions & knowledge

| Path | Role |
| --- | --- |
| [adr/](./adr/) | ADRs（含 ADR-004 MCP↔REST；ADR-006 ChatBox SSE；ADR-007 Key 密文；ADR-010 吊销按 user） |
| [knowledge/](./knowledge/) | 仓库备忘；**产品库入库正文**见 [`knowledge/for-kb/`](./knowledge/for-kb/) |

## Machine contracts

See [`../contracts/`](../contracts/) (`mcp-tools.json`, search response schema).
