# Contributing

Use a branch for each change and explain the user-visible behavior in your pull request. Keep code, tests, and documentation consistent. A branch name such as `feature/123-update-reports` should use the relevant issue number.

## Prepare the environment

Use Python 3.11 or newer. Create the Conda environment only if it doesn't already exist, then activate it before installing packages:

```bash
conda create -n prompt-evaluator python=3.11
conda activate prompt-evaluator
python -m pip install -r requirements.txt -r requirements-test.txt
python -m pip install -r requirements-parquet.txt
```

Parquet is optional for application users; installing its engine lets contributors exercise all format cases. Don't assume unconfigured pre-commit hooks are installed by the project.

## Validate changes offline

```bash
make test-core
make test-contract
python test_ci_features.py
python test_concurrent_basic.py
make lint
```

`make test-core` runs the curated groups, including the contract/workflow tests. New test files must be added to `tests/test_runner_simple.py` and the appropriate required CI job; discovery alone doesn't add them to the curated selection. API fixtures must match the documented request/response shapes. Never use customer data or credentials in fixtures.

The broader `python -m pytest tests/` suite includes known legacy reader/migration failures outside the curated selection. Don't hide failures or describe that broader suite as passing without checking it. See [testing](TESTING_GUIDE_SIMPLE.md) for scope and coverage.

`make format` checks formatting but can report existing legacy differences; `make format-fix` reformats the whole tree, so don't run it casually as part of an unrelated change. Limit formatting churn to code you own. `make type-check` runs the project's broader Mypy check.

## Live integration is separate

Offline tests don't need a tenant token and block network access. `make test-concurrent`, real evaluator commands, and `validate_setup.py --check-api` contact configured services. Only use them after confirming the target environment and authorization. Start with a small synthetic dataset and an isolated project; don't make live or load tests routine pull-request prerequisites.

## Document what users need

Keep the [README](../README.md), [public change summary](../CHANGES_SUMMARY.md), and relevant task guides current. Explain what changed for users before discussing implementation. Put internal test mechanics in contributor documentation, not in user release highlights.

Check documented option names against CLI help, use shipped sample paths, and label historical release records clearly. Keep the Markdown and [PDF quick reference](prompt_evaluator_cheat_sheet.pdf) aligned by regenerating the PDF from `CHEAT_SHEET.md` when it changes:

```bash
python docs/cheat_sheet_generator.py
```

Don't stage `.env`, generated evaluation results, or customer artifacts. `results/` is retained only through its empty `.gitkeep` placeholder. Review documentation and PDFs for sensitive examples before sharing.

Use four-space Python indentation, document nontrivial behavior, add regression tests, and keep review feedback focused and respectful. Describe validation and any remaining limitations accurately in the pull request.
