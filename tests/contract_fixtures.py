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

"""Synthetic OpenAPI response fixtures; no customer prompts or recorded credentials."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SPEC = json.loads((Path(__file__).resolve().parents[1] / "openapi.json").read_text())
STAMP = "2026-01-01T00:00:00Z"


def validate_schema(value, name):
    """Validate synthetic requests/responses against local references without fetching URLs."""
    schema = {"$ref": f"#/components/schemas/{name}", "components": SPEC["components"]}
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)


def api_body(endpoint="scans", outcome="flagged", error=False, scanners=True):
    """Build a schema-valid response with nullable recording/scanner identities."""
    result = {
        "outcome": outcome,
        "scannerResults": (
            [
                {
                    "outcome": "failed" if error or outcome != "cleared" else "passed",
                    "data": (
                        {"type": "error", "msg": "synthetic private diagnostic"}
                        if error
                        else {"type": "genai", "tokenUsage": 1}
                    ),
                    "scanDirection": "request",
                    "scannerName": None,
                    "scannerId": None,
                    "scannerVersionMeta": None,
                    "startedDate": STAMP,
                    "completedDate": STAMP,
                }
            ]
            if scanners
            else []
        ),
    }
    body = {"id": None, "result": result, "scanners": None}
    if endpoint == "scans":
        body["redactedInput"] = "synthetic sanitized input"
    else:
        result["response"] = None
        result["providerResult"] = None
    validate_schema(
        body, "PostScansResponse" if endpoint == "scans" else "PostPromptsResponse"
    )
    return body


class FakeResponse:
    """Minimal deterministic transport result; JSON errors never include real server data."""

    def __init__(self, body=None, status=200, json_error=False):
        self.body = body
        self.status_code = status
        self.json_error = json_error

    def json(self):
        """Return the fixture or simulate malformed JSON."""
        if self.json_error:
            raise ValueError("synthetic private server body")
        return self.body
