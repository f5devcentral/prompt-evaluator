# Prompt Evaluator — Quick-Start Cheat Sheet

## 1. Setup

```bash
git clone https://gitlab.com/Artemouse/prompt-evaluator.git
cd prompt-evaluator
```

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
CALYPSOAI_URL=https://calypsoai.app
CALYPSOAI_TOKEN=your_api_token_here
```

Verify everything is wired up:

```bash
python validate_setup.py
```

**Configure your guardrails:** In the CalypsoAI platform, enable only the guardrails relevant to your dataset. For example, if you're evaluating PII detection, enable the PII guardrails and disable others. This keeps results clean — cross-scanner interference will skew your metrics.

## 2. Run Your First Evaluation

```bash
# Full dataset
python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl

# Quick test — first 50 prompts only
python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl --lines 50
```

Results land in `results/` — including an **auto-generated PDF report**.

## 3. Two Evaluator Modes

| Mode | Script | API | Best for |
|------|--------|-----|----------|
| Standard | `prompt_evaluator.py` | `/scans` | Fast bulk evaluation — returns flagged/cleared only |
| Advanced | `prompt_evaluator_prompts.py` | `/prompts` | Deep analysis — full LLM responses and scanner details |

```bash
# Advanced mode
python prompt_evaluator_prompts.py --input datasets/sample-datasets/pii_dataset.jsonl --max-lines 50
```

## 4. Output Files

Every evaluation produces four files in `results/`:

```
results/
├── {dataset}_results.jsonl            # All scan results
├── {dataset}_false_positives.jsonl    # Safe prompts incorrectly blocked
├── {dataset}_false_negatives.jsonl    # Malicious prompts that slipped through
└── {dataset}_report.pdf               # Visual report with charts and analysis
```

## 5. Metrics Quick Reference

**Accuracy** — `(TP + TN) / Total`
Overall correctness. Useful as a gut check, but **can mislead on imbalanced datasets** — a scanner that always says "safe" scores high if most prompts are safe.

**Precision** — `TP / (TP + FP)`
"Of everything the scanner flagged, how much was actually bad?"
Low precision = too many false blocks = **frustrated legitimate users**.

**Recall** — `TP / (TP + FN)`
"Of everything that was actually bad, how much did we catch?"
Low recall = threats slipping through = **security gap**.

**F1 Score** — `2 × (Precision × Recall) / (Precision + Recall)`
Harmonic mean of precision and recall. **The single best metric when you need one number** to compare scanner configurations.

### Which metric matters most?

- **Security-first** (content moderation, PII detection) — prioritize **recall**. Missing a real threat is worse than a false alarm.
- **UX-first** (customer-facing chatbot) — prioritize **precision**. Blocking legitimate users erodes trust fast.
- **General comparison** — use **F1 score** as the tiebreaker.

### Benchmarks

| Metric | Good | Warning |
|--------|------|---------|
| Accuracy | > 85% | < 70% |
| Precision | > 90% | < 60% |
| Recall | > 90% | < 60% |
| F1 Score | > 80% | Large gap between precision and recall |

## 6. Generating Reports

Reports are **auto-generated** after every evaluation. To regenerate manually:

```bash
# Use the dataset NAME only — no path, no extension, no "_results" suffix
python report_generator.py --dataset pii_dataset
```

## 7. Re-Analyze Without Re-Scanning

Already have results? Recalculate metrics without burning API calls:

```bash
python evaluate_existing_results.py --input results/pii_dataset_results.jsonl
```

## 8. Common Flags

| Flag | Standard (`prompt_evaluator.py`) | Advanced (`prompt_evaluator_prompts.py`) |
|------|----------------------------------|------------------------------------------|
| Input file | `--input` / `-i` | `--input` / `-i` |
| Limit rows | `--lines` / `-l` | `--max-lines` / `-m` |
| Output file | `--output` / `-o` | `--output` / `-o` |
| FP/FN format | `--format` / `-f` | `--format` / `-f` |
| Results format | `--results-format` / `-r` | `--results-format` / `-r` |

Supported output formats: **json** (default), **csv**, **tsv**, **parquet**

---

*For deeper dives: [Evaluation Metrics](evaluation-metrics.md) · [PDF Reports](pdf-reports.md) · [Usage Guide](usage.md) · [Troubleshooting](troubleshooting.md)*
