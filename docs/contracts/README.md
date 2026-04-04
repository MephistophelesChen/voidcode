# Contract Documents

This directory is the source of truth for client-facing runtime contracts.

## Scope

These documents define the MVP contract layer shared by the runtime, CLI, future TUI, and future web client.

They are normative for:

- runtime event vocabulary
- client-facing session/run/stream API shapes
- approval request and resolution semantics
- runtime configuration surface and precedence
- stream transport behavior expected by clients

## Non-goals

These files do **not** define:

- implementation details for every runtime module
- post-MVP multi-agent protocols
- UI layout or visual design decisions
- GitHub backlog ownership or scheduling

## Current contract set

- [`runtime-events.md`](./runtime-events.md) — stable event vocabulary for client rendering
- [`client-api.md`](./client-api.md) — client-visible session/run/load/resume/stream contract
- [`approval-flow.md`](./approval-flow.md) — governed execution and approval semantics
- [`runtime-config.md`](./runtime-config.md) — MVP configuration surface and precedence
- [`stream-transport.md`](./stream-transport.md) — delivery and replay expectations for runtime streams

## Related issues

- #13 runtime event schema
- #14 client-facing API contract
- #15 approval schema
- #16 runtime configuration surface
- #17 stream transport abstraction

## Related code

- `src/voidcode/runtime/contracts.py`
- `src/voidcode/runtime/events.py`
- `src/voidcode/runtime/session.py`
- `src/voidcode/runtime/service.py`
- `src/voidcode/graph/contracts.py`
- `src/voidcode/tools/contracts.py`
- `src/voidcode/cli.py`

## Ownership rules

- Put schema details here, not in `README.md`, `docs/roadmap.md`, or `docs/current-state.md`.
- `docs/current-state.md` should describe what exists now, then link here for contract definitions.
- `docs/roadmap.md` should describe phases/epics only, then link here for contract prerequisites.
- GitHub issues should point to these files instead of restating the full schema in issue bodies.
