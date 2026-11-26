import os
from dataclasses import dataclass

from openai import OpenAI

from app.prompts import NOT_FOUND, SYSTEM_PROMPT


class ProvidersUnavailable(RuntimeError):
    """Every configured LLM provider failed."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    key_env: str
    model: str


GROQ_URL = "https://api.groq.com/openai/v1"
PROVIDERS = {
    "groq-120b": Provider("groq-120b", GROQ_URL, "GROQ_API_KEY", "openai/gpt-oss-120b"),
    "groq-20b": Provider("groq-20b", GROQ_URL, "GROQ_API_KEY", "openai/gpt-oss-20b"),
}
DEFAULT_ORDER = "groq-120b,groq-20b"


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[{i}] ({chunk['doc']}, page {chunk['page']})\n{chunk['content']}")
    return "\n\n".join(parts)


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    user = f"CONTEXT:\n{build_context(chunks)}\n\nQUESTION: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def call_provider(provider: Provider, messages: list[dict]) -> str:
    client = OpenAI(
        base_url=provider.base_url,
        api_key=os.environ[provider.key_env],
        timeout=30,
        max_retries=0,
    )
    response = client.chat.completions.create(
        model=provider.model,
        messages=messages,
        temperature=0.2,
        max_completion_tokens=1500,  # reasoning models spend part of this thinking
    )
    text = response.choices[0].message.content
    if not text or not text.strip():
        raise RuntimeError("empty response")
    return text.strip()


def complete_with_fallback(messages: list[dict], call=call_provider) -> str:
    order = os.environ.get("LLM_ORDER", DEFAULT_ORDER).split(",")
    errors = []
    for name in (n.strip() for n in order if n.strip()):
        try:
            return call(PROVIDERS[name], messages)
        except Exception as exc:  # noqa: BLE001 - any provider failure should trigger the fallback
            # type name only: messages can contain request details
            errors.append(f"{name}: {type(exc).__name__}")
    raise ProvidersUnavailable("All providers failed: " + "; ".join(errors))


def generate_answer(question: str, chunks: list[dict], complete=complete_with_fallback) -> str:
    if not chunks:
        return NOT_FOUND  # nothing retrieved, so don't ask a model to improvise
    return complete(build_messages(question, chunks))