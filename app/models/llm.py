from dataclasses import dataclass


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int | None

    completion_tokens: int | None

    total_tokens: int | None
