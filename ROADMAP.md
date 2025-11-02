Roadmap

Near-term (1–2 sprints)
- Coverage: Stabilize at or above 70% across matrix; raise CI gate to 75%, then 80%.
- Schema compatibility: Add a guard to compare contracts against last release tag (breaking changes require MAJOR bump flag).
- Logging: Add a smoke test for trace→log correlation (Tempo link present in Grafana Explore) to CI.

Mid-term
- API hardening: Contract tests for all public endpoints; enforce input validation at boundaries.
- Observability polish: Add golden traces for key flows to detect regressions in span structure.
- Security: Expand nightly audit and container scanning coverage; document threat model for preprocessing pipeline.

Longer-term
- Performance budgets: Introduce perf markers for heavy stages (OCR, table extraction) with guardrails in CI (opt-in job).
- Multi-tenant observability: Optional partitioned logs/metrics per tenant with labels and dashboards.
- Pluggable readers: Formal plugin interface for readers and per-plugin contracts.

Notes
- Most plan layers are already implemented in this repo; roadmap tracks incremental tightening and operational guardrails.

