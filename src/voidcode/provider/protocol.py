from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol, cast, runtime_checkable

from ..command.resolver import resolve_tool_instruction
from ..runtime.context_window import normalize_read_file_output
from ..tools.contracts import ToolCall, ToolDefinition, ToolResult

type AppliedSkill = dict[str, str]
type ProviderMessageRole = Literal["system", "user", "assistant", "tool"]
type ProviderStreamEventKind = Literal["delta", "content", "error", "done"]
type ProviderStreamChannel = Literal["text", "tool", "reasoning", "error"]
type ProviderDoneReason = Literal["completed", "cancelled", "error"]
type ProviderErrorKind = Literal[
    "missing_auth",
    "invalid_model",
    "rate_limit",
    "transient_failure",
    "context_limit",
    "unsupported_feature",
    "stream_tool_feedback_shape",
    "cancelled",
]


@runtime_checkable
class ProviderContextWindow(Protocol):
    @property
    def prompt(self) -> str: ...

    @property
    def tool_results(self) -> tuple[ToolResult, ...]: ...

    @property
    def compacted(self) -> bool: ...

    @property
    def retained_tool_result_count(self) -> int: ...

    @property
    def continuity_state(self) -> object | None: ...


@dataclass(frozen=True, slots=True)
class ProviderTurnRequest:
    available_tools: tuple[ToolDefinition, ...] = ()
    raw_model: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    assembled_context: ProviderAssembledContext | None = None
    prompt: str = ""
    tool_results: tuple[ToolResult, ...] = ()
    context_window: ProviderContextWindow | None = None
    applied_skills: tuple[AppliedSkill, ...] = ()
    skill_prompt_context: str = ""
    agent_preset: dict[str, object] | None = None
    attempt: int = 0
    abort_signal: ProviderAbortSignal | None = None

    def __post_init__(self) -> None:
        if self.assembled_context is not None:
            return
        prompt = self.prompt
        context_window = self.context_window
        tool_results = (
            context_window.tool_results if context_window is not None else self.tool_results
        )
        continuity_state = context_window.continuity_state if context_window is not None else None
        segments: list[ProviderContextSegment] = []
        skill_message = self.skill_prompt_context.strip()
        if not skill_message and self.applied_skills:
            rendered_skills: list[str] = []
            for skill in self.applied_skills:
                name = skill.get("name", "").strip() or "unnamed-skill"
                description = skill.get("description", "").strip()
                content = (
                    skill.get("prompt_context", "").strip() or skill.get("content", "").strip()
                )
                lines = [f"## {name}"]
                if description:
                    lines.append(f"Description: {description}")
                if content:
                    lines.append(content)
                rendered_skills.append("\n".join(lines))
            if rendered_skills:
                skill_message = (
                    "You must apply the following runtime-managed skills for this turn. "
                    "Treat them as active task instructions in addition to the user's request.\n\n"
                    + "\n\n".join(rendered_skills)
                )
        if skill_message:
            segments.append(ProviderContextSegment(role="system", content=skill_message))
        if continuity_state is not None:
            summary_text = getattr(continuity_state, "summary_text", None)
            if isinstance(summary_text, str) and summary_text.strip():
                segments.append(
                    ProviderContextSegment(
                        role="system",
                        content=f"Runtime continuity summary:\n{summary_text.strip()}",
                    )
                )
        segments.append(ProviderContextSegment(role="user", content=prompt))
        for index, result in enumerate(tool_results, start=1):
            raw_tool_call_id = result.data.get("tool_call_id")
            tool_call_id = (
                raw_tool_call_id
                if isinstance(raw_tool_call_id, str) and raw_tool_call_id.strip()
                else f"voidcode_tool_{index}"
            )
            raw_arguments = result.data.get("arguments")
            tool_arguments: dict[str, object]
            if isinstance(raw_arguments, dict):
                tool_arguments = dict(cast(dict[str, object], raw_arguments))
            else:
                tool_arguments = {}
            segments.append(
                ProviderContextSegment(
                    role="assistant",
                    content=None,
                    tool_call_id=tool_call_id,
                    tool_name=result.tool_name,
                    tool_arguments=tool_arguments,
                )
            )
            segments.append(
                ProviderContextSegment(
                    role="tool",
                    content=result.content or "",
                    tool_call_id=tool_call_id,
                    tool_name=result.tool_name,
                    metadata={
                        "status": result.status,
                        "error": result.error,
                        "data": result.data,
                        "truncated": result.truncated,
                        "partial": result.partial,
                        "reference": result.reference,
                    },
                )
            )
        object.__setattr__(
            self,
            "assembled_context",
            _LegacyAssembledContext(
                prompt=prompt,
                tool_results=tool_results,
                continuity_state=continuity_state,
                segments=tuple(segments),
                metadata={},
            ),
        )


@dataclass(frozen=True, slots=True)
class _LegacyAssembledContext:
    prompt: str
    tool_results: tuple[ToolResult, ...]
    continuity_state: object | None
    segments: tuple[ProviderContextSegmentLike, ...]
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class ProviderContextSegment:
    role: ProviderMessageRole
    content: str | None
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_arguments: dict[str, object] | None = None
    metadata: dict[str, object] | None = None


@runtime_checkable
class ProviderContextSegmentLike(Protocol):
    @property
    def role(self) -> ProviderMessageRole: ...

    @property
    def content(self) -> str | None: ...

    @property
    def tool_call_id(self) -> str | None: ...

    @property
    def tool_name(self) -> str | None: ...

    @property
    def tool_arguments(self) -> dict[str, object] | None: ...

    @property
    def metadata(self) -> dict[str, object] | None: ...


@runtime_checkable
class ProviderAssembledContext(Protocol):
    @property
    def prompt(self) -> str: ...

    @property
    def tool_results(self) -> tuple[ToolResult, ...]: ...

    @property
    def continuity_state(self) -> object | None: ...

    @property
    def segments(self) -> tuple[ProviderContextSegmentLike, ...]: ...

    @property
    def metadata(self) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class ProviderTokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    def metadata_payload(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
        }

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
        )


@dataclass(frozen=True, slots=True)
class ProviderTurnResult:
    tool_call: ToolCall | None = None
    output: str | None = None
    usage: ProviderTokenUsage | None = None


@runtime_checkable
class ProviderAbortSignal(Protocol):
    @property
    def cancelled(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class ProviderStreamEvent:
    kind: ProviderStreamEventKind
    channel: ProviderStreamChannel = "text"
    text: str | None = None
    error: str | None = None
    error_kind: ProviderErrorKind | None = None
    done_reason: ProviderDoneReason | None = None
    usage: ProviderTokenUsage | None = None


def normalize_provider_stream_event(event: ProviderStreamEvent) -> ProviderStreamEvent:
    if event.kind in {"delta", "content"} and event.text is None:
        raise ValueError(f"provider stream event '{event.kind}' requires text")
    if event.kind == "error" and event.error is None:
        raise ValueError("provider stream event 'error' requires error")
    if event.kind == "done" and event.done_reason is None:
        return ProviderStreamEvent(
            kind="done",
            channel=event.channel,
            done_reason="completed",
            usage=event.usage,
        )
    return event


def wrap_provider_stream(
    events: Iterator[ProviderStreamEvent],
    *,
    provider_name: str,
    model_name: str,
    abort_signal: ProviderAbortSignal | None,
    chunk_timeout_seconds: float,
) -> Iterator[ProviderStreamEvent]:
    if chunk_timeout_seconds <= 0:
        raise ValueError("provider stream chunk timeout must be greater than 0")

    if abort_signal is not None and abort_signal.cancelled:
        yield ProviderStreamEvent(
            kind="error",
            channel="error",
            error="provider stream cancelled",
            error_kind="cancelled",
        )
        yield ProviderStreamEvent(kind="done", done_reason="cancelled")
        return

    previous_chunk_at = time.monotonic()
    done_seen = False
    for event in events:
        now = time.monotonic()
        if now - previous_chunk_at > chunk_timeout_seconds:
            raise ProviderExecutionError(
                kind="transient_failure",
                provider_name=provider_name,
                model_name=model_name,
                message="provider stream chunk timeout exceeded",
            )
        previous_chunk_at = now

        if abort_signal is not None and abort_signal.cancelled:
            yield ProviderStreamEvent(
                kind="error",
                channel="error",
                error="provider stream cancelled",
                error_kind="cancelled",
            )
            yield ProviderStreamEvent(kind="done", done_reason="cancelled")
            return

        normalized = normalize_provider_stream_event(event)
        yield normalized
        if normalized.kind == "done":
            done_seen = True
            break

    if not done_seen:
        yield ProviderStreamEvent(kind="done", done_reason="completed")


@dataclass(frozen=True, slots=True)
class ProviderExecutionError(ValueError):
    kind: ProviderErrorKind
    provider_name: str
    model_name: str
    message: str
    retryable: bool = False
    details: dict[str, object] | None = None

    def __str__(self) -> str:
        return self.message


@runtime_checkable
class TurnProvider(Protocol):
    @property
    def name(self) -> str: ...

    def propose_turn(self, request: ProviderTurnRequest) -> ProviderTurnResult: ...


@runtime_checkable
class StreamableTurnProvider(Protocol):
    @property
    def name(self) -> str: ...

    def stream_turn(self, request: ProviderTurnRequest) -> Iterator[ProviderStreamEvent]: ...


@runtime_checkable
class ModelTurnProvider(Protocol):
    @property
    def name(self) -> str: ...

    def turn_provider(self) -> TurnProvider: ...


ModelProvider = ModelTurnProvider


@dataclass(frozen=True, slots=True)
class StubTurnProvider:
    name: str

    def propose_turn(self, request: ProviderTurnRequest) -> ProviderTurnResult:
        assembled_context = request.assembled_context
        if assembled_context is None:
            raise ValueError("assembled context is required")
        commands = [line.strip() for line in assembled_context.prompt.splitlines() if line.strip()]
        if not commands:
            raise ValueError("request must not be empty")

        step_index = len(assembled_context.tool_results)
        if step_index >= len(commands):
            if not assembled_context.tool_results:
                raise ValueError("request must contain at least one actionable command")
            last_result = assembled_context.tool_results[-1]
            return ProviderTurnResult(output=_normalize_tool_output(last_result.content))

        resolution = resolve_tool_instruction(
            commands[step_index],
            request.available_tools,
            unavailable_message_suffix="single-agent execution",
        )
        return ProviderTurnResult(tool_call=resolution.tool_call)


def _normalize_tool_output(content: str | None) -> str:
    normalized = normalize_read_file_output(content)
    return "" if normalized is None else normalized
