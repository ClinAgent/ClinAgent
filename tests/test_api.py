import asyncio
import json

import httpx
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from aegishealth.api.app import create_app
from aegishealth.api.schema import PatientInput
from aegishealth.api.service import clinical_query
from aegishealth.api.synthesis import CloudSynthesizer

PATIENT = dict(
    zip(
        [
            "age",
            "sex",
            "cp",
            "trestbps",
            "chol",
            "fbs",
            "restecg",
            "thalach",
            "exang",
            "oldpeak",
            "slope",
            "ca",
            "thal",
        ],
        [63, 1, 4, 145, 233, 1, 2, 150, 1, 2.3, 2, 0, 7],
    )
)
PREDICTION = {
    "disease_probability": 0.8,
    "top_3_contributors": [{"feature": "chol"}, {"feature": "thal"}, {"feature": "age"}],
}
EVIDENCE = [
    {"evidence_id": "E1", "text": "Evidence content"},
    {"evidence_id": "E2", "text": "Other content"},
]


class Agents:
    def analyze(self, patient):
        return {
            "prediction": PREDICTION,
            "evidence": EVIDENCE,
            "timings_ms": {},
            "retrieval_query": "test",
        }


def test_validation_and_partial_response(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    synth = CloudSynthesizer()
    with TestClient(create_app(Agents(), synth)) as client:
        assert client.get("/health").json()["cloud_configured"] is False
        response = client.post("/analyze", json=PATIENT)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "partial"
        assert body["synthesis"]["text"] is None
        assert body["synthesis"]["reason"] == "provider_not_configured"
        for field, value in [("age", True), ("age", "63"), ("thal", 2), ("chol", 0)]:
            bad = client.post("/analyze", json={**PATIENT, field: value})
            assert bad.status_code == 422
            assert all("input" not in e for e in bad.json()["detail"])
        assert client.post("/analyze", json={**PATIENT, "name": "not accepted"}).status_code == 422
        assert (
            client.post("/analyze", json={**PATIENT, "ca": None, "thal": None}).status_code == 200
        )


@pytest.mark.parametrize(
    "mode",
    ["valid", "timeout", "bad_json", "truncated", "bad_citation", "extra_sentence", "unauthorized"],
)
@pytest.mark.parametrize("provider", ["openrouter", "openai"])
def test_cloud_contract(monkeypatch, mode, provider):
    monkeypatch.setenv(f"{provider.upper()}_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    def handler(request):
        assert str(request.url) == (
            "https://openrouter.ai/api/v1/chat/completions" if provider == "openrouter"
            else "https://api.openai.com/v1/chat/completions"
        )
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        assert "reasoning_effort" not in payload
        if provider == "openrouter":
            assert payload["model"] == "openai/gpt-4.1-mini"
            assert payload["max_tokens"] == 1024
            assert payload["provider"] == {"require_parameters": True}
            assert "max_completion_tokens" not in payload
        else:
            assert payload["model"] == "gpt-4.1-mini"
            assert payload["max_completion_tokens"] == 1024
            assert "provider" not in payload
        assert payload["messages"][0]["role"] == "system"
        assert "untrusted data" in payload["messages"][0]["content"]
        assert len(payload["messages"]) == 2
        if mode == "timeout":
            raise httpx.ReadTimeout("test")
        if mode == "unauthorized":
            return httpx.Response(401, json={"error": "secret provider body"})
        content = {
            "sentences": [
                "The estimate is a research result.",
                "Contributors describe model associations.",
                "Review limited evidence with a clinician [E1].",
            ],
            "evidence_ids": ["E1"],
        }
        if mode == "bad_citation":
            content["evidence_ids"] = ["E9"]
        if mode == "extra_sentence":
            content["sentences"][0] = "One sentence. Another sentence."
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length" if mode == "truncated" else "stop",
                        "message": {
                            "content": "not json" if mode == "bad_json" else json.dumps(content)
                        },
                    }
                ]
            },
        )

    async def run():
        synth = CloudSynthesizer(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        result = await synth.summarize(PATIENT, PREDICTION, EVIDENCE)
        await synth.close()
        return result

    result = asyncio.run(run())
    assert result["status"] == ("complete" if mode == "valid" else "unavailable")
    if mode != "valid":
        assert result["text"] is None


def test_query_preserves_observed_feature_meaning():
    q = clinical_query({**PATIENT, "thal": None}, PREDICTION)
    assert "total cholesterol mg/dL: 233" in q
    assert "thallium" not in q
    assert "LDL" not in q
    assert PatientInput(**PATIENT).feature_array()[4] == 233


def test_openrouter_default_and_model_override(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "obsolete-key-not-for-openrouter")

    def unexpected_request(request):
        pytest.fail("Missing OpenRouter credentials must not trigger a request")

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(unexpected_request))
        synth = CloudSynthesizer(client=client)
        assert synth.provider == "openrouter"
        assert synth.model == "openai/gpt-4.1-mini"
        result = await synth.summarize(PATIENT, PREDICTION, EVIDENCE)
        assert result["reason"] == "provider_not_configured"
        await synth.close()
        monkeypatch.setenv("LLM_MODEL", "vendor/custom-model")
        synth = CloudSynthesizer()
        assert synth.model == "vendor/custom-model"
        await synth.close()

    asyncio.run(run())
