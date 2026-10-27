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

"""Small synchronous client for the scan and prompt OpenAPI operations.

Configuration is resolved only when a request is made. Imports and CLI help never
read credentials or contact a server; explicit environment values outrank dotenv.
"""

import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import requests
from dotenv import load_dotenv

DEFAULT_ORIGIN = "https://us1.calypsoai.app"
API_PATH = "/backend/v1"
OUTCOMES = frozenset(("cleared", "flagged", "blocked", "redacted"))


class APIError(Exception):
    """Expose a safe category/status, never a response body, URL, or credential."""

    def __init__(self, category, status_code=None):
        self.category = category
        self.status_code = status_code
        message = category.replace("_", " ")
        if status_code is not None:
            message += f" (HTTP {status_code})"
        super().__init__(message)


def normalize_base_url(value):
    """Accept an origin or API base; preserve reverse-proxy prefixes exactly once."""
    parts = urlsplit(value.strip())
    if (
        parts.scheme not in ("https", "http")
        or not parts.netloc
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
    ):
        raise ValueError("CALYPSOAI_URL must be an HTTP(S) origin or API base URL")
    path = parts.path.rstrip("/")
    if not path.endswith(API_PATH):
        path += API_PATH
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


@dataclass(frozen=True)
class APIConfig:
    """Request configuration; the token is deliberately excluded from repr."""

    base_url: str
    token: str = field(repr=False)
    timeout: float = 30.0

    @classmethod
    def from_environment(cls, timeout=None):
        """Load config lazily; timeout must be a finite, positive number of seconds."""
        load_dotenv(override=False)
        token = os.environ.get("CALYPSOAI_TOKEN")
        if not token or not token.strip():
            raise ValueError("CALYPSOAI_TOKEN environment variable not found")
        try:
            seconds = float(
                timeout
                if timeout is not None
                else os.environ.get("CALYPSOAI_TIMEOUT", 30)
            )
        except (TypeError, ValueError):
            raise ValueError("API timeout must be a positive number") from None
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("API timeout must be a finite, positive number")
        return cls(
            normalize_base_url(os.environ.get("CALYPSOAI_URL", DEFAULT_ORIGIN)),
            token,
            seconds,
        )

    @property
    def headers(self):
        """Return request headers without logging the bearer token."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


def safe_error_record(error):
    """Convert exceptions to non-sensitive persisted error metadata."""
    if isinstance(error, APIError):
        return {"error_category": error.category, "http_status": error.status_code}
    return {
        "error_category": (
            "configuration_error"
            if isinstance(error, ValueError)
            else "processing_error"
        )
    }


def _valid_timestamp(value):
    """Accept timezone-aware ISO timestamps, without echoing malformed content."""
    if not isinstance(value, str):
        return False
    try:
        return (
            datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
        )
    except ValueError:
        return False


def _scanner_results(value, diagnostics):
    """Validate consumed scan fields and retain safe evidence, not message content."""
    if not isinstance(value, list):
        raise APIError("invalid_response")
    results = []
    for scan in value:
        if (
            not isinstance(scan, dict)
            or scan.get("outcome") not in ("passed", "failed")
            or scan.get("scanDirection") not in ("request", "response")
            or not isinstance(scan.get("data"), dict)
            or not _valid_timestamp(scan.get("startedDate"))
            or not _valid_timestamp(scan.get("completedDate"))
        ):
            raise APIError("invalid_response")
        retained = {
            key: scan[key]
            for key in (
                "scannerId",
                "scannerName",
                "scannerVersionMeta",
                "outcome",
                "scanDirection",
                "startedDate",
                "completedDate",
                "customConfig",
            )
            if key in scan
        }
        retained["data"] = (
            scan["data"] if diagnostics else {"type": scan["data"].get("type")}
        )
        if diagnostics and "message" in scan:
            retained["message"] = scan["message"]
        results.append(retained)
    return results


def parse_result(body, endpoint, diagnostics=False):
    """Normalize a successful response; null recording IDs and LLM text are valid.

    Guardrail execution errors mark an incomplete evaluation. Provider failure is
    tracked separately and does not erase a usable guardrail classification.
    """
    if not isinstance(body, dict) or not isinstance(body.get("result"), dict):
        raise APIError("invalid_response")
    raw = body["result"]
    if not isinstance(raw.get("outcome"), str) or raw["outcome"] not in OUTCOMES:
        raise APIError("invalid_outcome")
    scans = _scanner_results(raw.get("scannerResults"), diagnostics)
    if endpoint == "scans" and not isinstance(body.get("redactedInput"), str):
        raise APIError("invalid_response")
    response = raw.get("response")
    if response is not None and not isinstance(response, str):
        raise APIError("invalid_response")
    incomplete = any(scan["data"].get("type") == "error" for scan in scans)
    result = {
        "outcome": raw["outcome"],
        "status": "incomplete" if incomplete else "ok",
        "scanner_results": scans,
        "request_id": body.get("id"),
        "evaluation_mode": endpoint,
    }
    if incomplete:
        result["error_category"] = "guardrail_error"
    if endpoint == "prompts":
        result["response"] = response
        provider = raw.get("providerResult")
        if provider is not None:
            if (
                not isinstance(provider, dict)
                or type(provider.get("statusCode")) is not int
                or not _valid_timestamp(provider.get("sentDate"))
                or not _valid_timestamp(provider.get("receivedDate"))
            ):
                raise APIError("invalid_response")
            result["provider_result"] = {
                key: provider[key]
                for key in ("statusCode", "sentDate", "receivedDate")
                if key in provider
            }
            result["provider_error"] = not 200 <= provider["statusCode"] < 300
    if diagnostics:
        if endpoint == "scans":
            result["redacted_input"] = body["redactedInput"]
        if body.get("scanners") is not None:
            result["scanners"] = body["scanners"]
    return result


def send_request(
    endpoint,
    prompt,
    *,
    project=None,
    provider=None,
    verbose=False,
    diagnostics=False,
    timeout=None,
    session=None,
    config=None,
):
    """POST one string input and return evidence plus elapsed seconds.

    Only the two supported synchronous operations are accepted. Requests are not
    automatically replayed: their recording/provider side effects aren't idempotent.
    """
    if endpoint not in ("scans", "prompts"):
        raise ValueError("Unsupported evaluation endpoint")
    if not isinstance(prompt, str):
        raise ValueError("Prompt input must be a string")
    config = config or APIConfig.from_environment(timeout)
    payload = {"input": prompt, "verbose": bool(verbose or diagnostics)}
    if endpoint == "scans":
        payload["flagOnly"] = True
    if project is not None:
        payload["project"] = project
    if provider is not None and endpoint == "prompts":
        payload["provider"] = provider
    start = time.perf_counter()
    transport = session if session is not None else requests
    try:
        response = transport.post(
            f"{config.base_url}/{endpoint}",
            headers=config.headers,
            json=payload,
            timeout=config.timeout,
        )
        if not 200 <= response.status_code < 300:
            code = response.status_code
            category = {
                401: "authentication_error",
                403: "permission_error",
                422: "validation_error",
                429: "rate_limit",
            }.get(code, "server_error" if code >= 500 else "http_error")
            raise APIError(category, code)
        try:
            body = response.json()
        except ValueError:
            raise APIError("invalid_json") from None
        result = parse_result(body, endpoint, diagnostics)
    except requests.Timeout:
        raise APIError("timeout") from None
    except requests.RequestException:
        raise APIError("connection_error") from None
    result["response_time"] = time.perf_counter() - start
    result["project"] = project
    if endpoint == "prompts":
        result["provider"] = provider
    return result
