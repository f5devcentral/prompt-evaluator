#!/usr/bin/env python3
"""
Cheat Sheet PDF Generator for Prompt Evaluator

Generates a professional, customer-ready PDF cheat sheet covering setup,
evaluation commands, output files, metrics, and common flags.

Uses the same ReportLab + matplotlib stack as report_generator.py.
"""

import os
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
except ImportError:
    print("reportlab is required. Install with: pip install reportlab")
    raise

from matplotlib import pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Color palette — matches report_generator.py
# ---------------------------------------------------------------------------
DARK_BLUE = colors.HexColor('#2C3E50')
ACCENT_BLUE = colors.HexColor('#3498DB')
SECTION_TEXT = colors.HexColor('#34495E')
GREEN = colors.HexColor('#2ECC71')
RED = colors.HexColor('#E74C3C')
ORANGE = colors.HexColor('#F39C12')
LIGHT_BG = colors.HexColor('#F8F9FA')
CODE_BG = colors.HexColor('#1E1E2E')       # Dark editor background
CODE_TEXT = colors.HexColor('#A9B7C6')      # Light grey-blue code text
CODE_KEYWORD = colors.HexColor('#CC7832')   # Orange for keywords/flags
CODE_STRING = colors.HexColor('#6A8759')    # Green for values
CODE_ACCENT = colors.HexColor('#3498DB')    # Left-border accent


def _build_styles():
    """Create paragraph styles consistent with the evaluation reports."""
    styles = getSampleStyleSheet()

    def _add(style_obj):
        try:
            styles.add(style_obj)
        except (AttributeError, KeyError, ValueError):
            pass

    _add(ParagraphStyle(
        name='DocTitle', parent=styles['Heading1'],
        fontSize=28, textColor=DARK_BLUE, spaceAfter=8,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    ))
    _add(ParagraphStyle(
        name='Subtitle', parent=styles['Normal'],
        fontSize=13, textColor=SECTION_TEXT, spaceAfter=30,
        fontName='Helvetica', alignment=TA_CENTER
    ))
    _add(ParagraphStyle(
        name='SectionHeader', parent=styles['Heading2'],
        fontSize=16, textColor=ACCENT_BLUE, spaceAfter=14,
        spaceBefore=24, fontName='Helvetica-Bold'
    ))
    _add(ParagraphStyle(
        name='Body', parent=styles['Normal'],
        fontSize=10, textColor=DARK_BLUE, spaceAfter=10,
        leading=15
    ))
    _add(ParagraphStyle(
        name='CodeInner', parent=styles['Normal'],
        fontSize=9, textColor=CODE_TEXT,
        fontName='Courier', leading=14,
        spaceAfter=0, spaceBefore=0
    ))
    _add(ParagraphStyle(
        name='SmallNote', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=6, leading=12
    ))
    return styles


# ---------------------------------------------------------------------------
# Code block helper — dark editor-style block with accent left border
# ---------------------------------------------------------------------------
def _code_block(text, styles):
    """Render code inside a dark rounded-corner-style block with a left accent bar."""
    inner = Paragraph(text, styles['CodeInner'])
    # Two-column table: narrow accent bar | code content
    t = Table(
        [[' ', inner]],
        colWidths=[4, 6.5 * inch],
    )
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), CODE_ACCENT),     # left accent bar
        ('BACKGROUND', (1, 0), (1, 0), CODE_BG),         # dark code bg
        ('TOPPADDING', (1, 0), (1, 0), 10),
        ('BOTTOMPADDING', (1, 0), (1, 0), 10),
        ('LEFTPADDING', (1, 0), (1, 0), 12),
        ('RIGHTPADDING', (1, 0), (1, 0), 12),
        ('TOPPADDING', (0, 0), (0, 0), 0),
        ('BOTTOMPADDING', (0, 0), (0, 0), 0),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 0),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [0, 4, 4, 0]),
    ]))
    # Wrap in a list with spacers so there's breathing room above and below
    return [
        Spacer(1, 6),
        t,
        Spacer(1, 10),
    ]


# ---------------------------------------------------------------------------
# Chart: metrics importance visual
# ---------------------------------------------------------------------------
def _generate_metrics_priority_chart():
    """Bar chart showing metric priority by use case."""
    fig, ax = plt.subplots(figsize=(6.5, 3.2))

    categories = ['Security-First', 'UX-First', 'General']
    metrics = ['Recall', 'Precision', 'F1 Score']
    # Relative importance weights (illustrative)
    data = {
        'Recall':    [0.95, 0.50, 0.75],
        'Precision': [0.55, 0.95, 0.75],
        'F1 Score':  [0.70, 0.70, 0.95],
    }

    x = np.arange(len(categories))
    width = 0.25
    palette = ['#E74C3C', '#3498DB', '#F39C12']

    for i, (metric, vals) in enumerate(data.items()):
        bars = ax.bar(x + i * width, vals, width, label=metric, color=palette[i])

    ax.set_ylabel('Relative Priority', fontsize=10, fontweight='bold')
    ax.set_title('Which Metric Matters Most?', fontsize=12, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------
HEADER_STYLE = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT_BLUE),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('TOPPADDING', (0, 0), (-1, 0), 10),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')]),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 1), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
])


def _styled_table(data, col_widths):
    t = Table(data, colWidths=col_widths)
    t.setStyle(HEADER_STYLE)
    return t


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------
def generate_cheat_sheet(output_path=None):
    """Build the cheat-sheet PDF and write it to disk."""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__),
                                   'prompt_evaluator_cheat_sheet.pdf')
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        rightMargin=0.65 * inch, leftMargin=0.65 * inch,
        topMargin=0.65 * inch, bottomMargin=0.65 * inch
    )

    S = _build_styles()
    story = []

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    story.append(Spacer(1, 1.4 * inch))
    story.append(Paragraph("Prompt Evaluator", S['DocTitle']))
    story.append(Paragraph("Quick-Start Cheat Sheet", S['Subtitle']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(
        width="80%", thickness=1, color=ACCENT_BLUE,
        spaceAfter=12, spaceBefore=12
    ))
    story.append(Paragraph(
        "Everything you need to go from zero to a full scanner evaluation — "
        "setup, commands, output files, and what the metrics actually mean.",
        S['Body']
    ))
    story.append(PageBreak())

    # ------------------------------------------------------------------
    # 1. Setup
    # ------------------------------------------------------------------
    story.append(Paragraph("1. Setup", S['SectionHeader']))
    story.append(Paragraph("Clone the repository:", S['Body']))
    story.extend(_code_block(
        "git clone https://gitlab.com/Artemouse/prompt-evaluator.git<br/>"
        "cd prompt-evaluator",
        S
    ))
    story.append(Paragraph("Install dependencies:", S['Body']))
    story.extend(_code_block("pip install -r requirements.txt", S))
    story.append(Paragraph(
        "Create a <b>.env</b> file in the project root:", S['Body']
    ))
    story.extend(_code_block(
        "CALYPSOAI_URL=https://calypsoai.app<br/>"
        "CALYPSOAI_TOKEN=your_api_token_here",
        S
    ))
    story.append(Paragraph("Verify the setup:", S['Body']))
    story.extend(_code_block("python validate_setup.py", S))
    story.append(Paragraph(
        "<b>Configure your guardrails:</b> In the CalypsoAI platform, enable only the "
        "guardrails relevant to your dataset. For example, if you're evaluating PII "
        "detection, enable the PII guardrails and disable others. This keeps results "
        "clean — cross-scanner interference will skew your metrics.",
        S['Body']
    ))

    # ------------------------------------------------------------------
    # 2. Run Your First Evaluation
    # ------------------------------------------------------------------
    story.append(Paragraph("2. Run Your First Evaluation", S['SectionHeader']))
    story.extend(_code_block(
        "python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl",
        S
    ))
    story.append(Paragraph(
        "Limit to the first 50 prompts for a quick test:", S['Body']
    ))
    story.extend(_code_block(
        "python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl --lines 50",
        S
    ))
    story.append(Paragraph(
        "Results — including an <b>auto-generated PDF report</b> — land in the "
        "<font face='Courier' size='9'>results/</font> directory.",
        S['Body']
    ))

    # ------------------------------------------------------------------
    # 3. Two Evaluator Modes
    # ------------------------------------------------------------------
    story.append(Paragraph("3. Two Evaluator Modes", S['SectionHeader']))
    mode_data = [
        ['Mode', 'Script', 'API', 'Best For'],
        ['Standard', 'prompt_evaluator.py', '/scans',
         'Fast bulk evaluation — flagged/cleared only'],
        ['Advanced', 'prompt_evaluator_prompts.py', '/prompts',
         'Deep analysis — full LLM responses & scanner details'],
    ]
    story.append(_styled_table(mode_data,
                               [0.9 * inch, 2.2 * inch, 0.8 * inch, 3.0 * inch]))
    story.append(Spacer(1, 0.15 * inch))
    story.extend(_code_block(
        "python prompt_evaluator_prompts.py "
        "--input datasets/sample-datasets/pii_dataset.jsonl --max-lines 50",
        S
    ))

    # ------------------------------------------------------------------
    # 4. Output Files
    # ------------------------------------------------------------------
    story.append(Paragraph("4. Output Files", S['SectionHeader']))
    story.append(Paragraph(
        "Every evaluation produces four files in "
        "<font face='Courier' size='9'>results/</font>:",
        S['Body']
    ))
    files_data = [
        ['File', 'Contents'],
        ['{dataset}_results.jsonl', 'All scan results with outcome and timing'],
        ['{dataset}_false_positives.jsonl', 'Safe prompts incorrectly blocked'],
        ['{dataset}_false_negatives.jsonl', 'Malicious prompts that slipped through'],
        ['{dataset}_report.pdf', 'Visual report with charts and analysis'],
    ]
    story.append(_styled_table(files_data, [3.0 * inch, 4.0 * inch]))

    story.append(PageBreak())

    # ------------------------------------------------------------------
    # 5. Metrics Quick Reference
    # ------------------------------------------------------------------
    story.append(Paragraph("5. Metrics Quick Reference", S['SectionHeader']))

    metrics_data = [
        ['Metric', 'Formula', 'What It Tells You'],
        ['Accuracy',
         '(TP + TN) / Total',
         'Overall correctness. Can mislead on imbalanced datasets.'],
        ['Precision',
         'TP / (TP + FP)',
         '"Of everything flagged, how much was actually bad?" '
         'Low precision = frustrated users.'],
        ['Recall',
         'TP / (TP + FN)',
         '"Of everything actually bad, how much did we catch?" '
         'Low recall = security gap.'],
        ['F1 Score',
         '2 × (P × R) / (P + R)',
         'Harmonic mean of precision & recall. '
         'Best single number for comparison.'],
    ]
    story.append(_styled_table(metrics_data,
                               [1.0 * inch, 1.6 * inch, 4.3 * inch]))
    story.append(Spacer(1, 0.2 * inch))

    # Confusion matrix key
    story.append(Paragraph("<b>Confusion Matrix Key</b>", S['Body']))
    story.append(Spacer(1, 0.05 * inch))
    cm_data = [
        ['', 'Scanner: Flagged', 'Scanner: Cleared'],
        ['Actually Malicious',
         'True Positive (TP) — correct catch',
         'False Negative (FN) — missed threat'],
        ['Actually Safe',
         'False Positive (FP) — false alarm',
         'True Negative (TN) — correct pass'],
    ]
    cm_table = Table(cm_data, colWidths=[1.4 * inch, 2.7 * inch, 2.7 * inch])
    cm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('BACKGROUND', (0, 1), (0, -1), DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#D5F5E3')),  # TP
        ('BACKGROUND', (2, 2), (2, 2), colors.HexColor('#D5F5E3')),  # TN
        ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#FADBD8')),  # FN
        ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#FADBD8')),  # FP
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(cm_table)
    story.append(Spacer(1, 0.25 * inch))

    # "Which metric matters most?" chart
    chart_buf = _generate_metrics_priority_chart()
    story.append(Image(chart_buf, width=5.5 * inch, height=2.8 * inch))
    story.append(Spacer(1, 0.15 * inch))

    priority_data = [
        ['Use Case', 'Prioritize', 'Why'],
        ['Security-first (PII, content mod)', 'Recall',
         'Missing a real threat is worse than a false alarm.'],
        ['UX-first (customer chatbot)', 'Precision',
         'Blocking legitimate users erodes trust fast.'],
        ['General comparison', 'F1 Score',
         'Best single number that balances both concerns.'],
    ]
    story.append(_styled_table(priority_data,
                               [2.2 * inch, 1.0 * inch, 3.7 * inch]))
    story.append(Spacer(1, 0.2 * inch))

    # Benchmarks
    story.append(Paragraph("<b>Benchmarks</b>", S['Body']))
    story.append(Spacer(1, 0.05 * inch))
    bench_data = [
        ['Metric', 'Good', 'Warning'],
        ['Accuracy', '> 85%', '< 70%'],
        ['Precision', '> 90%', '< 60%'],
        ['Recall', '> 90%', '< 60%'],
        ['F1 Score', '> 80%', 'Large gap between precision and recall'],
    ]
    story.append(_styled_table(bench_data,
                               [1.2 * inch, 1.2 * inch, 4.5 * inch]))

    story.append(PageBreak())

    # ------------------------------------------------------------------
    # 6. Generating Reports
    # ------------------------------------------------------------------
    story.append(Paragraph("6. Generating Reports", S['SectionHeader']))
    story.append(Paragraph(
        "PDF reports are <b>auto-generated</b> after every evaluation. "
        "To regenerate manually:",
        S['Body']
    ))
    story.extend(_code_block(
        "python report_generator.py --dataset pii_dataset",
        S
    ))
    story.append(Paragraph(
        "Use the dataset <b>name only</b> — no path, no extension, "
        "no <font face='Courier' size='9'>_results</font> suffix.",
        S['Body']
    ))

    # ------------------------------------------------------------------
    # 7. Re-Analyze Without Re-Scanning
    # ------------------------------------------------------------------
    story.append(Paragraph("7. Re-Analyze Without Re-Scanning", S['SectionHeader']))
    story.append(Paragraph(
        "Already have results? Recalculate metrics without burning API calls:",
        S['Body']
    ))
    story.extend(_code_block(
        "python evaluate_existing_results.py --input results/pii_dataset_results.jsonl",
        S
    ))

    # ------------------------------------------------------------------
    # 8. Common Flags
    # ------------------------------------------------------------------
    story.append(Paragraph("8. Common Flags", S['SectionHeader']))
    flags_data = [
        ['Flag', 'Standard (prompt_evaluator.py)',
         'Advanced (prompt_evaluator_prompts.py)'],
        ['Input file', '--input / -i', '--input / -i'],
        ['Limit rows', '--lines / -l', '--max-lines / -m'],
        ['Output file', '--output / -o', '--output / -o'],
        ['FP/FN format', '--format / -f', '--format / -f'],
        ['Results format', '--results-format / -r', '--results-format / -r'],
    ]
    story.append(_styled_table(flags_data,
                               [1.3 * inch, 2.7 * inch, 2.9 * inch]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Supported output formats: <b>json</b> (default), "
        "<b>csv</b>, <b>tsv</b>, <b>parquet</b>",
        S['Body']
    ))

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor('#BDC3C7'),
        spaceAfter=8, spaceBefore=8
    ))
    story.append(Paragraph(
        "For deeper dives see the full documentation: "
        "Evaluation Metrics · PDF Reports · Usage Guide · Troubleshooting",
        S['SmallNote']
    ))

    # Build
    doc.build(story)
    print(f"Cheat sheet PDF generated: {output_path}")
    return output_path


if __name__ == '__main__':
    generate_cheat_sheet()
