# Approval Flow Contract

Source issue: #15

## Purpose

Define the MVP governed-execution contract for approval decisions around write-capable or risky actions.

## Status

The current deterministic runtime emits a permission event with `decision=allow`, but the full governed approval flow is not implemented yet.

## Current code anchors

- permission responsibility is assigned to the runtime in `docs/architecture.md`
- current runtime emits `runtime.permission_resolved` in `src/voidcode/runtime/service.py`
- current payload includes:
  - `tool`
  - `decision`

## MVP decision vocabulary

- `allow`: execution proceeds
- `deny`: execution does not proceed
- `ask`: execution pauses until an explicit client or operator decision is recorded

## Approval request contract

An approval request must be representable with at least:

- `session_id`
- `sequence`
- `tool`
- `reason` or risk context
- proposed arguments or target summary
- current policy context

This should be emitted as a runtime event rather than as client-only UI state.

## Approval resolution contract

An approval resolution must be able to record:

- `session_id`
- the request being resolved
- `decision`: `allow` / `deny`
- optional operator note
- timestamp or ordering marker sufficient for resume/replay

## MVP invariants

- approval state belongs to the runtime, not the client
- write/risky tool execution may not bypass the approval contract
- `ask` requires a resumable paused state
- clients must be able to render pending approval vs resolved approval distinctly

## Current vs planned behavior

Current deterministic behavior:
- read-only flow emits `runtime.permission_resolved` with `decision=allow`
- there is no persisted approval request queue yet
- there is no `ask` or `deny` execution path implemented yet

Planned MVP behavior:
- runtime can pause on `ask`
- clients can resolve approvals against runtime state
- persisted sessions can replay approval history and resume correctly

## Related clients

- CLI may display approval events in text form
- TUI should support direct approval interaction
- web client should render approval state from runtime events and persisted state

## Non-goals

- multi-user approval workflows
- role-based policy systems
- advanced post-MVP approval policy matrices

## Acceptance checks

- a write-capable request can be represented as pending approval before execution
- resumed sessions preserve unresolved or resolved approval state accurately
- clients do not need custom per-client approval logic to interpret the runtime state
