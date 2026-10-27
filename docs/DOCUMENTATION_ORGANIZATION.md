# Documentation organization

Organize documentation by the task a reader wants to complete. The [documentation index](README.md) is the navigation entry point, and the [project README](../README.md) provides a working introduction.

## User-facing information

[What's changed](../CHANGES_SUMMARY.md) explains user-visible improvements and compatibility notes without internal implementation or investigation details. [Installation](installation.md) and [usage](usage.md) cover setup and current commands. [Dataset guidance](datasets.md) and [format guidance](IMPROVED_DATASET_FORMATS.md) explain inputs and utility limitations.

[Metrics](evaluation-metrics.md), [result formats](results-format-changes.md), and [PDF reports](pdf-reports.md) explain what outputs mean, which defaults apply, and how to revisit saved work. Keep sensitive-data guidance close to any workflow that creates or shares artifacts.

The [quick reference](CHEAT_SHEET.md) is the source for the generated [PDF cheat sheet](prompt_evaluator_cheat_sheet.pdf). Regenerate it with `python docs/cheat_sheet_generator.py` when its content changes.

## Contributor information

[Testing](TESTING_GUIDE_SIMPLE.md), [contributing](contributing.md), and the [tools README](../tools/README.md) describe development checks and utility interfaces. Place schema filenames, CI gates, and implementation details here when they're needed by contributors, rather than making them the public release narrative.

## Historical records

Keep release dates and original release records intact. Mark [v2.0 release notes](RELEASE_NOTES_v2.0.md) as historical and link current instructions; old commands, roadmap items, or compatibility promises aren't guarantees of today's behavior.

## Maintenance

Check option names, default output formats, shipped sample paths, and link targets when a workflow changes. Use file or heading links instead of brittle line numbers and file-length claims. Document known limitations rather than advertising unverified streaming, rollback, performance, or metadata guarantees. No real tenant calls are needed to validate documentation links or CLI option names.
