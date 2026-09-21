import httpx
import pytest

from aegishealth.evaluate import evaluate_http, precision_at_k


def test_precision_penalizes_missing_and_duplicate_results():
    assert precision_at_k(["a", "b"], ["a", "b"]) == 1
    assert precision_at_k(["a", "a"], ["a"]) == 0.5
    assert precision_at_k([], ["a"]) == 0
    with pytest.raises(ValueError):
        precision_at_k([], [], 0)


def test_partial_http_results_never_pass_latency_target(monkeypatch):
    original = httpx.Client

    def handler(request):
        return httpx.Response(
            200,
            json={
                "status": "partial",
                "synthesis": {"status": "unavailable", "reason": "provider_not_configured"},
            },
        )

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )
    result = evaluate_http("http://test", requests=2)
    assert result["complete_requests"] == 0
    assert result["target_met"] is False
    assert result["complete_p95_seconds"] is None


def test_only_complete_pipeline_is_timed_as_success(monkeypatch):
    original = httpx.Client

    def handler(request):
        return httpx.Response(200, json={"status": "complete", "synthesis": {"status": "complete"}})

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )
    result = evaluate_http("http://test", requests=2)
    assert result["complete_requests"] == 2
    assert result["target_met"] is True
