# Changelog - MedFlux

All notable changes to this project will be documented here.

## [v0.1.0] - 2025-10-26
- Initial internal versioning structure implemented.

## [Unreleased]
- feat(monitoring): added full observability stack (metrics + tracing + dashboards)
  - Tracing sampler + OTLP endpoint config, service metadata
  - API request spans + metrics exemplars
  - Grafana dashboards and Prometheus alerts
  - Alertmanager Slack routing via env
