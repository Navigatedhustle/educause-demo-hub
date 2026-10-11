# EDUCAUSE Demo Hub

A local demo launcher and lifecycle controller that serializes heavyweight workloads and exposes readiness, stop and failure handling in native and browser menus.

**Maturity:** Operational integration utility. Four isolated startup/failure checks pass. Full demo transitions were not run because they would stop or start existing workloads. It remains a deployment-specific integration utility.

## How it works

Native GTK menu and browser companion → shared Python controller → per-demo launcher scripts, readiness polling and tracked processes. It adopts an already healthy Atlas lane and stops tracked workloads during transitions.

## Getting started

Read [installation, configuration and shutdown](docs/OPERATIONS.md) and [model/data retrieval](docs/MODELS.md). Review [dependency evidence](docs/DEPENDENCIES.md) before choosing an environment. The safe review launcher uses loopback and does not install services or load models.

## Security and data

Read [security and safe updates](SECURITY.md) and [ownership/license status](docs/LICENSE-STATUS.md). Runtime originals are preserved separately. This is a sanitized source snapshot with new history: no account state, business records, model weights, unknown media assets or original logs/history are distributed. Third-party notices included in this copy remain applicable.

## Verification

See [verification evidence and limitations](docs/VERIFICATION.md). Tests distinguish synthetic/mocked workflows from live integrations. Original demo screenshots and document recordings are excluded; use the synthetic workflow in the operations guide for your own reviewed demonstration.

## Roadmap

Replace host-specific launcher wiring with a validated configuration file; add non-disruptive readiness diagnostics and richer process-identity safeguards; run transition rehearsals only in a dedicated operator window.

For route/source details see [architecture](docs/ARCHITECTURE.md).
