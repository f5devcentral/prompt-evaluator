# Installation

Use Python 3.11 or newer in Conda. Python 3.11 is the CI baseline. Activate an existing project environment before installing packages; create one only if needed.

```bash
conda create -n prompt-evaluator python=3.11
conda activate prompt-evaluator
python -m pip install -r requirements.txt
# Development and contract tests:
python -m pip install -r requirements-test.txt
# Optional Parquet input/output engine:
python -m pip install -r requirements-parquet.txt
```

Pandas alone doesn't guarantee Parquet support. Missing engines produce an actionable error rather than silently switching to JSONL.

## Configure API access

```dotenv
CALYPSOAI_URL=https://us1.calypsoai.app
CALYPSOAI_TOKEN=your_api_token_here
CALYPSOAI_TIMEOUT=30
```

Use `https://eu1.calypsoai.app` for EU1 or your approved tenant origin. A full API base ending in `/backend/v1` is also accepted. URL credentials, query strings, and fragments are rejected. Don't put tokens in URLs or commit `.env`.

Explicit environment values override `.env`. The optional timeout is a finite, positive number of seconds and defaults to 30; `--timeout` overrides it. Requests doesn't impose a total run deadline, so wall time can include connection setup and executor queueing.

## Validate locally first

```bash
python validate_setup.py
python validate_setup.py --dataset datasets/sample-datasets/pii_dataset.jsonl
make validate
```

These commands check local dependencies and output permissions. Dataset checks are optional and use the enhanced reader. No credentials are needed and no network calls are made by default.

Only after confirming the target tenant, opt into a bounded connectivity/authentication probe:

```bash
python validate_setup.py --check-api
```

The probe reads `GET /backend/v1/scanners?limit=1`; it doesn't create scans or change configuration. A 401 is an authentication failure. A 403 means the token can't list scanners and doesn't establish whether scanning is permitted.

## Choose the evaluation configuration

Use an isolated project containing only the relevant guardrails, selected with `--project`. Prompts mode can select a configured provider with `--provider`; omission uses the selected project's default. Confirm infrastructure approval before concurrent evaluation and use synthetic input first.

See [usage](usage.md) and [sensitive result handling](results-format-changes.md).
