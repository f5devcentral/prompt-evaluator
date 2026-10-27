# Copyright 2026 Andy Ryan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Offline compatibility tests against the downloaded OpenAPI contract."""

import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest
import requests

import calypsoai_client as client
from evaluation_common import calculate_metrics, error_result
from tests.contract_fixtures import FakeResponse, STAMP, api_body, validate_schema


@pytest.mark.parametrize("endpoint", ["scans", "prompts"])
@pytest.mark.parametrize("outcome", ["cleared", "flagged", "blocked", "redacted"])
def test_payload_and_outcome_contract(monkeypatch, endpoint, outcome):
    """Assert URL/auth/options and preserve each valid raw outcome, including null IDs."""
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        validate_schema(
            kwargs["json"],
            "PostScansBody" if endpoint == "scans" else "PostPromptsBody",
        )
        return FakeResponse(api_body(endpoint, outcome))

    monkeypatch.setattr(requests, "post", post)
    result = client.send_request(
        endpoint,
        "synthetic input",
        project="test-project",
        provider="test-provider",
        timeout=7,
    )
    url, options = calls[0]
    assert url == f"https://test.calypsoai.app/backend/v1/{endpoint}"
    assert options["headers"]["Authorization"].startswith("Bearer ")
    assert options["timeout"] == 7
    assert options["json"]["project"] == "test-project"
    if endpoint == "scans":
        assert options["json"]["flagOnly"] is True
        assert "provider" not in options["json"]
    else:
        assert options["json"]["provider"] == "test-provider"
        assert result["response"] is None
    assert result["outcome"] == outcome
    assert result["request_id"] is None
    assert result["status"] == "ok"
    assert result["response_time"] >= 0
    assert len(calls) == 1


@pytest.mark.parametrize("endpoint", ["scans", "prompts"])
def test_empty_scanners_and_omitted_optionals(monkeypatch, endpoint):
    """Recording-disabled responses and legitimately empty scanner arrays remain usable."""
    body = api_body(endpoint, scanners=False)
    body.pop("id")
    body.pop("scanners")
    monkeypatch.setattr(requests, "post", lambda *a, **kw: FakeResponse(body))
    result = client.send_request(endpoint, "synthetic")
    assert result["scanner_results"] == []
    assert result["request_id"] is None


@pytest.mark.parametrize(
    "status,category",
    [
        (401, "authentication_error"),
        (403, "permission_error"),
        (422, "validation_error"),
        (429, "rate_limit"),
        (500, "server_error"),
        (503, "server_error"),
        (404, "http_error"),
    ],
)
def test_safe_http_failures(monkeypatch, status, category):
    """HTTP failures are categorized without retaining bodies or replaying POSTs."""
    calls = []

    def post(*args, **kwargs):
        calls.append(1)
        return FakeResponse({"private": "synthetic private server body"}, status)

    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(client.APIError) as caught:
        client.send_request("scans", "synthetic")
    assert caught.value.category == category
    assert caught.value.status_code == status
    assert "private" not in str(caught.value)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "exception,category",
    [
        (requests.Timeout("synthetic private content"), "timeout"),
        (requests.ConnectionError("synthetic private content"), "connection_error"),
    ],
)
def test_safe_transport_failures(monkeypatch, exception, category):
    """Timeout/connection exceptions never leak their arbitrary exception strings."""

    def post(*args, **kwargs):
        raise exception

    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(client.APIError) as caught:
        client.send_request("scans", "synthetic")
    assert caught.value.category == category
    assert "private" not in str(caught.value)


def test_invalid_json(monkeypatch):
    """Malformed JSON is an explicit error, not an invented safe outcome."""
    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: FakeResponse(json_error=True)
    )
    with pytest.raises(client.APIError, match="invalid json"):
        client.send_request("scans", "synthetic")


@pytest.mark.parametrize(
    "mutation",
    [
        "result",
        "scannerResults",
        "outcome",
        "unknown_outcome",
        "redactedInput",
        "scanDirection",
        "data",
        "startedDate",
        "completedDate",
        "bad_timestamp",
    ],
)
def test_malformed_required_evidence(mutation):
    """Reject missing/invalid required fields while optional/null fields stay valid."""
    body = api_body()
    scan = body["result"]["scannerResults"][0]
    if mutation in ("result", "redactedInput"):
        body.pop(mutation)
    elif mutation in ("scannerResults", "outcome"):
        body["result"].pop(mutation)
    elif mutation == "unknown_outcome":
        body["result"]["outcome"] = "future-value"
    elif mutation == "bad_timestamp":
        scan["startedDate"] = "not-a-timestamp"
    else:
        scan.pop(mutation)
    with pytest.raises(client.APIError):
        client.parse_result(body, "scans")


def test_guardrail_error_and_opt_in_diagnostics(monkeypatch):
    """Scanner errors are incomplete; private diagnostic messages require explicit opt-in."""
    body = api_body(error=True)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: FakeResponse(body))
    safe = client.send_request("scans", "synthetic")
    detailed = client.send_request("scans", "synthetic", diagnostics=True)
    assert safe["status"] == "incomplete"
    assert "msg" not in safe["scanner_results"][0]["data"]
    assert "redacted_input" not in safe
    assert "msg" in detailed["scanner_results"][0]["data"]
    assert detailed["redacted_input"] == body["redactedInput"]
    scores = calculate_metrics([dict(safe, expected=True)])
    assert scores["total"] == 0
    assert scores["incomplete_count"] == 1


def test_provider_failure_is_separate_from_detection():
    """A provider failure neither invents a detection nor erases usable guardrail evidence."""
    body = api_body("prompts", "cleared")
    body["result"]["providerResult"] = {
        "statusCode": 503,
        "sentDate": STAMP,
        "receivedDate": STAMP,
        "data": "synthetic private provider body",
    }
    validate_schema(body, "PostPromptsResponse")
    parsed = client.parse_result(body, "prompts")
    metrics = calculate_metrics([dict(parsed, expected=False)])
    assert metrics["true_negative"] == 1
    assert metrics["provider_error_count"] == 1
    assert "data" not in parsed["provider_result"]
    for field in ("sentDate", "receivedDate", "statusCode"):
        invalid = copy.deepcopy(body)
        invalid["result"]["providerResult"].pop(field)
        with pytest.raises(client.APIError):
            client.parse_result(invalid, "prompts")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://us1.calypsoai.app", "https://us1.calypsoai.app/backend/v1"),
        (
            "https://eu1.calypsoai.app/backend/v1/",
            "https://eu1.calypsoai.app/backend/v1",
        ),
        ("https://tenant.example/prefix/", "https://tenant.example/prefix/backend/v1"),
        (
            "https://tenant.example/prefix/backend/v1",
            "https://tenant.example/prefix/backend/v1",
        ),
    ],
)
def test_url_normalization(url, expected):
    """Origins, API bases, and reverse-proxy prefixes normalize exactly once."""
    assert client.normalize_base_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "ftp://tenant.example",
        "https://user:password@tenant.example",
        "https://tenant.example?token=synthetic",
        "not-a-url",
    ],
)
def test_invalid_origins(url):
    """Reject credential-bearing or ambiguous configured URLs without printing them."""
    with pytest.raises(ValueError):
        client.normalize_base_url(url)


@pytest.mark.parametrize("timeout", [0, -1, "bad", float("nan"), float("inf")])
def test_invalid_timeout(timeout):
    """Unbounded/nonpositive timeout configuration fails before any request."""
    with pytest.raises(ValueError):
        client.APIConfig.from_environment(timeout)


def test_configuration_precedence_and_safe_repr(monkeypatch, tmp_path):
    """Explicit environment wins over synthetic dotenv and token repr stays hidden."""
    from dotenv import load_dotenv

    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text(
        "CALYPSOAI_URL=https://ignored.example\nCALYPSOAI_TOKEN=synthetic-file-token\n"
    )
    monkeypatch.setattr(
        client,
        "load_dotenv",
        lambda override=False: load_dotenv(dotenv_file, override=override),
    )
    # Session isolation replaces dotenv.load_dotenv; use its implementation for this one synthetic file.
    from dotenv.main import load_dotenv as real_load

    monkeypatch.setattr(
        client,
        "load_dotenv",
        lambda override=False: real_load(dotenv_file, override=override),
    )
    assert client.APIConfig.from_environment().base_url.startswith(
        "https://test.calypsoai.app/"
    )
    config = client.APIConfig.from_environment()
    assert config.token not in repr(config)
    monkeypatch.delenv("CALYPSOAI_TOKEN")
    monkeypatch.setattr(client, "load_dotenv", lambda **kw: False)
    with pytest.raises(ValueError, match="CALYPSOAI_TOKEN"):
        client.APIConfig.from_environment()
    monkeypatch.delenv("CALYPSOAI_URL")
    monkeypatch.setenv("CALYPSOAI_TOKEN", "synthetic-only")
    assert (
        client.APIConfig.from_environment().base_url
        == client.DEFAULT_ORIGIN + client.API_PATH
    )


@pytest.mark.parametrize(
    "module",
    [
        "prompt_evaluator",
        "prompt_evaluator_prompts",
        "prompt_evaluator_concurrent",
        "report_generator",
        "validate_setup",
    ],
)
def test_import_and_help_need_no_credentials_or_io(tmp_path, module):
    """Import/help must not call dotenv or HTTP, even with no configured token."""
    root = Path(__file__).resolve().parents[1]
    script = (
        "import runpy,sys; from unittest.mock import patch; "
        f"sys.argv=[{module!r},'--help']; "
        "guard=patch('dotenv.load_dotenv',side_effect=AssertionError('dotenv called')); guard.start(); "
        "network=patch('requests.sessions.Session.request',side_effect=AssertionError('network called')); network.start(); "
        f"runpy.run_path({str(root / (module + '.py'))!r},run_name='__main__')"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=tmp_path,
        env={
            "PATH": os.defpath,
            "HOME": str(tmp_path),
            "PYTHONPATH": str(root),
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_invalid_operation_and_input():
    """Unsupported endpoints and non-string input fail locally."""
    with pytest.raises(ValueError):
        client.send_request("models", "synthetic")
    with pytest.raises(ValueError):
        client.send_request("scans", {})
    row = error_result(
        {"prompt": "synthetic", "expected": True}, RuntimeError("private")
    )
    assert row["error_category"] == "processing_error"
    assert "private" not in str(row)
