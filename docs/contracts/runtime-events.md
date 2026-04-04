# Runtime Event Schema

Source issue: #13

## Purpose

Define the MVP event vocabulary emitted by the runtime for client rendering.

## Status

This schema documents the current single-agent MVP contract. It is intentionally narrower than any future multi-agent protocol.

## Canonical envelope

Current in-code shape from `src/voidcode/runtime/events.py`:

```python
EventEnvelope(
    session_id: str,
    sequence: int,
    event_type: str,
    source: Literal["runtime", "graph", "tool"],
    payload: dict[str, object],
)
```

## Field rules

- `session_id`: required; identifies the owning session
- `sequence`: required; monotonically increasing within a session response or replay
- `event_type`: required; string identifier for the event kind
- `source`: required; one of `runtime`, `graph`, or `tool`
- `payload`: required as a field, may be an empty object

## MVP invariants

- events are session-scoped
- events are ordered by `sequence`
- clients must preserve event order when rendering a turn or replay
- clients must tolerate unknown `event_type` values by rendering them generically rather than failing
- clients must treat `payload` as extensible

## Known event types emitted today

From `src/voidcode/runtime/service.py` and the deterministic read-only slice:

- `runtime.request_received`
- `graph.tool_request_created`
- `runtime.tool_lookup_succeeded`
- `runtime.permission_resolved`
- `runtime.tool_completed`

Additional graph finalization events may be emitted by the graph layer and are part of the same ordered stream.

## Current integration-test event sequence

The current deterministic read-only integration tests assert this ordered sequence:

1. `runtime.request_received`
2. `graph.tool_request_created`
3. `runtime.tool_lookup_succeeded`
4. `runtime.permission_resolved`
5. `runtime.tool_completed`
6. `graph.response_ready`

This sequence is the most concrete client-visible MVP event flow implemented today.

## Current payload expectations

### `runtime.request_received`
- source: `runtime`
- current payload:
  - `prompt: str`

### `graph.tool_request_created`
- source: `graph`
- current payload:
  - `tool: str`
  - `path: object`

### `runtime.tool_lookup_succeeded`
- source: `runtime`
- current payload:
  - `tool: str`

### `runtime.permission_resolved`
- source: `runtime`
- current payload:
  - `tool: str`
  - `decision: str`

### `runtime.tool_completed`
- source: `tool`
- current payload:
  - tool-defined result data

## Client rendering requirements

- CLI may render events as formatted lines
- TUI and web clients should render the ordered stream as timeline/activity data
- clients should not infer approvals, failures, or tool completion from text output alone when event data is available

## Non-goals

- multi-agent event semantics
- token/cost telemetry schema
- provider-specific model reasoning events

## Acceptance checks

- a client can replay a persisted session using only the stored event sequence and output
- event ordering is sufficient to show request → tool request → permission → tool completion → response ready
- adding a new event type does not break older clients that use generic fallback rendering
