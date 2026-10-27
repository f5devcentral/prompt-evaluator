# Testing

The curated offline suites are the standard development checks. They use synthetic data and don't require a CalypsoAI token. Live tenant behavior is a separate integration check, not something unit tests establish.

## Prepare the project environment

Activate the existing Conda environment, or create it as described in [installation](installation.md). Install test dependencies there:

```bash
conda activate prompt-evaluator
python -m pip install -r requirements.txt -r requirements-test.txt
python -m pip install -r requirements-parquet.txt
```

The Parquet engine is optional for normal use, but needed to exercise those cases locally. The required CI contract job installs it.

## Run the curated suites

```bash
make test-core
make test-contract
python test_ci_features.py
python test_concurrent_basic.py
```

`make test-core` runs all registered groups. For a narrower selection:

```bash
make test-simple
make test-converter
make test-reader
make test-integration
```

The core group checks dataset utilities. The reader and integration groups intentionally select specific tests rather than all cases in their files. Don't describe those selections as complete coverage of every legacy feature.

The contract group exercises client requests/responses, all supported overall outcomes, safe error handling, shared metric/export membership, result-format round trips, actual mocked CLI dispatch, PDF generation, output preflight, and concurrent scheduling. Synthetic fixtures are checked against the API description in `openapi.json`.

Its coverage gate is 80% scoped to `calypsoai_client.py` and `evaluation_common.py`, not a claim about whole-project coverage. Formatting and critical lint checks are separate.

## Test isolation

Tests disable dotenv loading and block HTTP/socket access before collection. Explicit mocks provide responses. Imports and `--help` must work without credentials or network calls. Tests should write only to temporary paths and preserve any existing user artifacts.

Don't use real prompts, PII, credentials, or live response exports as test fixtures. Use synthetic examples with the necessary structure and edge cases instead.

## Broader discovery and known limitations

```bash
python -m pytest tests/ -v
```

This runs additional legacy reader/migration tests outside the curated selection. Some are known to fail because their expectations don't match current utility interfaces or because legacy utility behavior is incomplete. Keep those failures visible and distinguish them from regressions in the feature being changed.

In particular, a selected reader test doesn't establish bounded-memory streaming, every metadata-conversion path, or every auto-detected legacy format. Measure performance on representative inputs rather than relying on universal time/memory guarantees.

## Continuous integration

GitHub Actions is configured for Python 3.11. Required jobs cover core utilities, conversion, selected reader/integration cases, contract/workflow checks, and CLI features. Lint and security jobs remain non-blocking.

Register new suites explicitly in `tests/test_runner_simple.py` and the relevant required CI job. Use the same interpreter for local checks and dependency installation. Avoid broad formatter or dependency changes unrelated to the work under review.

## Checks that are not offline unit tests

`make test-concurrent` and evaluator runs contact the configured tenant. `validate_setup.py --check-api` makes a read-only scanner-list request. Confirm the environment, permissions, and intended data before opting in; load tests also need infrastructure approval.

`make ci-github` installs dependencies and runs additional quality/security checks. `setup_testing.py` is an optional provisioning utility that installs dependencies and writes sample/environment-template files, not a Conda environment creator. Neither is necessary just to run the curated tests.

See [contributing](contributing.md) for documentation and review expectations.
