import pytest

from app.answer import ProvidersUnavailable, complete_with_fallback


def test_all_providers_failing_raises_providers_unavailable(monkeypatch):
    monkeypatch.setenv("LLM_ORDER", "groq-120b,groq-20b")

    def fail(provider, messages):
        raise TimeoutError("slow")

    with pytest.raises(ProvidersUnavailable):
        complete_with_fallback([], call=fail)