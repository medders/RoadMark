---
title: Platform Roadmap
description: Roadmap for the platform team
owner: Jane Smith
team: Platform Team
team_link: https://example.com/platform
last_updated: 2026-03-21
summary: |
  This quarter we're focused on reliability and developer experience.
  The gateway upgrade and auth refactor are our top priorities;
  observability work unblocks both of them. Owner: @admin
---

## Now

### API Gateway Upgrade
- summary: Replace the legacy gateway with a high-throughput layer to meet SLA commitments.
- objectives:
  - Improve throughput by 30%
  - Reduce p99 latency below 50 ms
- status: in-progress
- confidence: committed
- target: Q2 2026
- stakeholders:
  - CTO
  - @admin
- components:
  - API
  - Gateway
- jira: PLAT-101
- link: https://example.com/wiki/api-gateway-upgrade

### Auth Refactor
- summary: Migrate session tokens to a compliant storage mechanism.
- objectives:
  - Remove legacy session store
  - Implement short-lived JWT rotation
- status: blocked
- confidence: likely
- target: Q2 2026
- stakeholder: Security Lead
- component: Auth

## Next

### Observability Improvements
- objectives:
  - Add distributed tracing across all services
  - Centralise log aggregation
- status: planned
- confidence: likely
- target: Q3 2026

### Developer Portal
- summary: Self-service tooling so teams can ship without a platform ticket.
- status: planned
- confidence: exploring

## Later

### Multi-region Support
- summary: Active-active deployment across EU and US to meet data-residency requirements.
- status: planned
- confidence: exploring

### Event Streaming Platform
- summary: Replace polling patterns with an event-driven architecture.
- status: planned
- confidence: exploring
