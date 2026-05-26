#!/usr/bin/env python3
"""
Comparative Scanner Evaluation Report Generator

Produces a comprehensive, customer-facing PDF comparing:
  - Prompt Injection (PI) Only
  - Prompt Injection + PII

across two datasets:
  - LMSYS Toxic Chat Test  (mixed-class, 1.8% malicious)
  - OpenSafetyLab Salad-Data Train  (100% malicious, adversarial)

Output: results/comparative_scanner_analysis_report.pdf
Usage:  conda run -n prompt-evaluator python comparative_report_generator.py
"""

import os
import json
import sys
import numpy as np
from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable, KeepTogether,
)

# =============================================================================
# CONSTANTS
# =============================================================================

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
OUTPUT_PATH = os.path.join(RESULTS_DIR, "comparative_scanner_analysis_report.pdf")

# Four evaluation configurations: (dataset, scanner-config) pairs
CONFIGS = [
    {
        "key": "lmsys_pi",
        "dataset_label": "LMSYS Toxic Chat",
        "config_label": "PI Only",
        "results_file": "lmsys_toxic_chat_test_results.jsonl",
        "fp_file": "lmsys_toxic_chat_test_false_positives.jsonl",
        "fn_file": "lmsys_toxic_chat_test_false_negatives.jsonl",
    },
    {
        "key": "lmsys_pii",
        "dataset_label": "LMSYS Toxic Chat",
        "config_label": "PI + PII",
        "results_file": "lmsys_toxic_chat_test-pii_results.jsonl",
        "fp_file": "lmsys_toxic_chat_test-pii_false_positives.jsonl",
        "fn_file": "lmsys_toxic_chat_test-pii_false_negatives.jsonl",
    },
    {
        "key": "salad_pi",
        "dataset_label": "Salad Attack Prompts",
        "config_label": "PI Only",
        "results_file": "OpenSafetyLab_Salad_Data_train_results.jsonl",
        "fp_file": "OpenSafetyLab_Salad_Data_train_false_positives.jsonl",
        "fn_file": "OpenSafetyLab_Salad_Data_train_false_negatives.jsonl",
    },
    {
        "key": "salad_pii",
        "dataset_label": "Salad Attack Prompts",
        "config_label": "PI + PII",
        "results_file": "OpenSafetyLab_Salad_Data_train-pii_results.jsonl",
        "fp_file": "OpenSafetyLab_Salad_Data_train-pii_false_positives.jsonl",
        "fn_file": "OpenSafetyLab_Salad_Data_train-pii_false_negatives.jsonl",
    },
]

# Brand palette
C_BLUE   = '#3498DB'
C_GREEN  = '#2ECC71'
C_RED    = '#E74C3C'
C_ORANGE = '#F39C12'
C_DARK   = '#2C3E50'
C_GRAY   = '#7F8C8D'
C_LGRAY  = '#ECF0F1'
C_PURPLE = '#9B59B6'


# =============================================================================
# DATA LOADING & METRICS
# =============================================================================

def load_jsonl(path):
    records = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return records


def compute_metrics(records):
    """Return confusion matrix counts, derived rates, latency stats, prompt-size stats."""
    tp = tn = fp = fn = 0
    response_times = []
    prompt_sizes = []

    for r in records:
        expected = str(r.get('expected', '')).strip().lower()
        outcome  = str(r.get('outcome',  '')).strip().lower()

        if   expected == 'true'  and outcome == 'flagged':  tp += 1
        elif expected == 'false' and outcome == 'cleared':  tn += 1
        elif expected == 'false' and outcome == 'flagged':  fp += 1
        elif expected == 'true'  and outcome == 'cleared':  fn += 1

        rt = r.get('response_time')
        if rt is not None:
            try:
                response_times.append(float(rt))
            except (ValueError, TypeError):
                pass

        ps = r.get('prompt_size')
        if ps is not None:
            try:
                prompt_sizes.append(int(ps))
            except (ValueError, TypeError):
                pass

    total          = tp + tn + fp + fn
    safe_total     = fp + tn
    malicious_total = tp + fn

    accuracy  = (tp + tn) / total if total > 0 else 0.0
    prec_d    = tp + fp
    precision = tp / prec_d if prec_d > 0 else None   # None when no safe prompts
    rec_d     = tp + fn
    recall    = tp / rec_d if rec_d > 0 else 0.0
    pr        = precision or 0.0
    f1_d      = pr + recall
    f1        = 2 * pr * recall / f1_d if f1_d > 0 else 0.0
    fpr_d     = fp + tn
    fpr       = fp / fpr_d if fpr_d > 0 else None     # None when all malicious
    fnr_d     = fn + tp
    fnr       = fn / fnr_d if fnr_d > 0 else 0.0

    latency = {}
    if response_times:
        arr = np.array(response_times)
        latency = dict(
            mean  = float(np.mean(arr)),
            min   = float(np.min(arr)),
            max   = float(np.max(arr)),
            p50   = float(np.percentile(arr, 50)),
            p95   = float(np.percentile(arr, 95)),
            p99   = float(np.percentile(arr, 99)),
            stdev = float(np.std(arr)),
            raw   = arr,
        )

    psize_stats = {}
    if prompt_sizes:
        arr = np.array(prompt_sizes)
        psize_stats = dict(
            mean = float(np.mean(arr)),
            min  = int(np.min(arr)),
            max  = int(np.max(arr)),
            p50  = float(np.percentile(arr, 50)),
            p95  = float(np.percentile(arr, 95)),
        )

    return dict(
        tp=tp, tn=tn, fp=fp, fn=fn,
        total=total, safe_total=safe_total, malicious_total=malicious_total,
        accuracy=accuracy, precision=precision, recall=recall, f1=f1,
        fpr=fpr, fnr=fnr,
        latency=latency, prompt_size=psize_stats,
    )


def load_all_data():
    data = {}
    for cfg in CONFIGS:
        key     = cfg['key']
        records = load_jsonl(os.path.join(RESULTS_DIR, cfg['results_file']))
        metrics = compute_metrics(records)
        fps     = load_jsonl(os.path.join(RESULTS_DIR, cfg['fp_file']))
        fns     = load_jsonl(os.path.join(RESULTS_DIR, cfg['fn_file']))
        data[key] = dict(config=cfg, records=records, metrics=metrics,
                         false_positives=fps, false_negatives=fns)
        print(f"  {key}: {len(records):,} records | "
              f"TP={metrics['tp']:,} TN={metrics['tn']:,} "
              f"FP={metrics['fp']:,} FN={metrics['fn']:,}")
    return data


# =============================================================================
# CHART GENERATORS  (return raw PNG bytes for safe multi-use)
# =============================================================================

def _save_fig(fig, dpi=150):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return buf.getvalue()


def _img(png_bytes, w_in, h_in):
    """Create a fresh ReportLab Image from stored PNG bytes."""
    return Image(BytesIO(png_bytes), width=w_in * inch, height=h_in * inch)


def chart_confusion_matrix_grid(data):
    """2×2 grid: rows = PI / PI+PII, cols = lmsys / salad."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))
    fig.suptitle('Confusion Matrices — All Configurations', fontsize=14,
                 fontweight='bold')

    combos = [
        ('lmsys_pi',  'lmsys_pii',  'LMSYS Toxic Chat'),
        ('salad_pi',  'salad_pii',  'Salad Attack Prompts'),
    ]
    row_titles = ['PI Only', 'PI + PII']

    for col, (k_pi, k_pii, ds_label) in enumerate(combos):
        for row, key in enumerate([k_pi, k_pii]):
            ax  = axes[row][col]
            m   = data[key]['metrics']
            mat = np.array([[m['tp'], m['fn']],
                            [m['fp'], m['tn']]], dtype=float)
            mx  = max(mat.max(), 1)
            ax.imshow(mat, cmap='RdYlGn', vmin=0, vmax=mx, aspect='auto')
            for i in range(2):
                for j in range(2):
                    v   = int(mat[i, j])
                    clr = 'white' if mat[i, j] / mx > 0.55 else 'black'
                    ax.text(j, i, f'{v:,}', ha='center', va='center',
                            fontsize=13, fontweight='bold', color=clr)
            ax.set_xticks([0, 1]);  ax.set_xticklabels(['Flagged', 'Cleared'], fontsize=9)
            ax.set_yticks([0, 1]);  ax.set_yticklabels(['Malicious', 'Safe'],  fontsize=9)
            ax.set_title(f'{ds_label}\n{row_titles[row]}', fontsize=10, fontweight='bold')

    fig.tight_layout()
    return _save_fig(fig)


def chart_grouped_metrics(data):
    """Grouped bar chart: Accuracy / Precision / Recall / F1 for all 4 configs."""
    keys   = ['lmsys_pi', 'lmsys_pii', 'salad_pi', 'salad_pii']
    xlbls  = ['lmsys\nPI Only', 'lmsys\nPI+PII', 'Salad\nPI Only', 'Salad\nPI+PII']
    mnames = ['Accuracy', 'Precision', 'Recall', 'F1']
    mcols  = [C_BLUE, C_GREEN, C_RED, C_ORANGE]

    x, width = np.arange(len(keys)), 0.18
    fig, ax  = plt.subplots(figsize=(11, 6))

    for i, (mn, mc) in enumerate(zip(mnames, mcols)):
        vals = []
        for k in keys:
            m = data[k]['metrics']
            if   mn == 'Accuracy':  v = m['accuracy']  * 100
            elif mn == 'Precision': v = (m['precision'] or 0) * 100
            elif mn == 'Recall':    v = m['recall']    * 100
            else:                   v = m['f1']         * 100
            vals.append(v)
        bars = ax.bar(x + i * width - 1.5 * width, vals, width, label=mn,
                      color=mc, alpha=0.85, edgecolor='white')
        for bar, v in zip(bars, vals):
            if v > 1:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                        f'{v:.0f}%', ha='center', va='bottom', fontsize=7.5,
                        fontweight='bold')

    ax.set_xticks(x); ax.set_xticklabels(xlbls, fontsize=10)
    ax.set_ylim(0, 118)
    ax.set_ylabel('Score (%)', fontsize=11)
    ax.set_title('Performance Metrics — All Configurations', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.text(0.01, 0.98, '* Precision N/A for Salad (no safe prompts)',
            transform=ax.transAxes, ha='left', va='top', fontsize=7.5,
            color=C_GRAY, style='italic')
    fig.tight_layout()
    return _save_fig(fig)


def chart_fpr_fnr(data):
    """Side-by-side FPR / FNR bar chart for all 4 configs."""
    keys  = ['lmsys_pi', 'lmsys_pii', 'salad_pi', 'salad_pii']
    xlbls = ['lmsys\nPI Only', 'lmsys\nPI+PII', 'Salad\nPI Only', 'Salad\nPI+PII']
    fpr_v = [(data[k]['metrics']['fpr'] or 0) * 100 for k in keys]
    fnr_v = [(data[k]['metrics']['fnr'] or 0) * 100 for k in keys]

    x, w  = np.arange(len(keys)), 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar(x - w / 2, fpr_v, w, label='FPR', color=C_ORANGE, alpha=0.85, edgecolor='white')
    b2 = ax.bar(x + w / 2, fnr_v, w, label='FNR', color=C_RED,    alpha=0.85, edgecolor='white')

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                        f'{h:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xticks(x); ax.set_xticklabels(xlbls, fontsize=10)
    ymax = max(max(fpr_v), max(fnr_v)) * 1.3 + 5
    ax.set_ylim(0, ymax)
    ax.set_ylabel('Rate (%)', fontsize=11)
    ax.set_title('False Positive Rate vs False Negative Rate', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.text(0.98, 0.98, '* Salad FPR = 0 (no safe prompts in dataset)',
            transform=ax.transAxes, ha='right', va='top', fontsize=7.5,
            color=C_GRAY, style='italic')
    fig.tight_layout()
    return _save_fig(fig)


def chart_latency(data):
    """Percentile bar chart + box plot for latency across 4 configs."""
    keys  = ['lmsys_pi', 'lmsys_pii', 'salad_pi', 'salad_pii']
    xlbls = ['lmsys\nPI Only', 'lmsys\nPI+PII', 'Salad\nPI Only', 'Salad\nPI+PII']
    clrs  = [C_BLUE, C_PURPLE, C_GREEN, C_ORANGE]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- left: grouped percentile bars ---
    x, w = np.arange(len(keys)), 0.18
    pct_defs = [('Mean', C_BLUE), ('p50', C_GREEN), ('p95', C_ORANGE), ('p99', C_RED)]
    for i, (pl, pc) in enumerate(pct_defs):
        vals = []
        for k in keys:
            lat = data[k]['metrics']['latency']
            vals.append(lat.get(pl.lower(), lat.get('mean', 0)) if lat else 0)
        ax1.bar(x + i * w - 1.5 * w, vals, w, label=pl, color=pc, alpha=0.85, edgecolor='white')

    ax1.set_xticks(x); ax1.set_xticklabels(xlbls, fontsize=9)
    ax1.set_ylabel('Seconds', fontsize=10)
    ax1.set_title('Latency Percentiles', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)

    # --- right: box plot ---
    raw = []
    for k in keys:
        lat = data[k]['metrics']['latency']
        raw.append(lat['raw'] if lat and 'raw' in lat else np.array([0.0]))
    bp = ax2.boxplot(raw, tick_labels=xlbls, patch_artist=True,
                     medianprops=dict(color='black', linewidth=2),
                     flierprops=dict(marker='o', markersize=2, alpha=0.3))
    for patch, c in zip(bp['boxes'], clrs):
        patch.set_facecolor(c); patch.set_alpha(0.7)
    ax2.set_ylabel('Seconds', fontsize=10)
    ax2.set_title('Latency Distribution', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)

    fig.tight_layout()
    return _save_fig(fig)


def chart_pii_delta(data):
    """Delta bar charts showing what changed when PII scanner was added."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    for col, (ds_label, k_pi, k_pii) in enumerate([
        ('LMSYS Toxic Chat',      'lmsys_pi', 'lmsys_pii'),
        ('Salad Attack Prompts',  'salad_pi',  'salad_pii'),
    ]):
        ax   = axes[col]
        m_pi  = data[k_pi]['metrics']
        m_pii = data[k_pii]['metrics']

        dtp = m_pii['tp'] - m_pi['tp']
        dtn = m_pii['tn'] - m_pi['tn']
        dfp = m_pii['fp'] - m_pi['fp']
        dfn = m_pii['fn'] - m_pi['fn']

        lbls = ['ΔTP', 'ΔTN', 'ΔFP', 'ΔFN']
        vals = [dtp, dtn, dfp, dfn]
        # TP↑ good, TN↑ good, FP↑ bad, FN↑ bad
        bar_clrs = [
            C_GREEN if dtp >= 0 else C_RED,
            C_GREEN if dtn >= 0 else C_RED,
            C_RED   if dfp >= 0 else C_GREEN,
            C_RED   if dfn >= 0 else C_GREEN,
        ]

        bars = ax.bar(lbls, vals, color=bar_clrs, alpha=0.85, edgecolor='white')
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    v + (max(abs(x) for x in vals) * 0.03) * (1 if v >= 0 else -1),
                    f'{v:+d}',
                    ha='center', va='bottom' if v >= 0 else 'top',
                    fontsize=12, fontweight='bold')

        ax.axhline(0, color='black', linewidth=0.8)
        ax.set_title(f'{ds_label}\nDelta: PI+PII − PI Only', fontsize=10, fontweight='bold')
        ax.set_ylabel('Count change', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    fig.tight_layout()
    return _save_fig(fig)


# =============================================================================
# STYLE HELPERS
# =============================================================================

def build_styles():
    s = getSampleStyleSheet()

    def add(style):
        try:
            s.add(style)
        except (KeyError, ValueError):
            pass

    add(ParagraphStyle('RptTitle',      parent=s['Heading1'], fontSize=26,
                       textColor=colors.HexColor(C_DARK), spaceAfter=16,
                       fontName='Helvetica-Bold', alignment=TA_CENTER))
    add(ParagraphStyle('RptSubtitle',   parent=s['Normal'],   fontSize=13,
                       textColor=colors.HexColor(C_GRAY), spaceAfter=8,
                       fontName='Helvetica', alignment=TA_CENTER))
    add(ParagraphStyle('RptSection',    parent=s['Heading2'], fontSize=15,
                       textColor=colors.HexColor(C_BLUE), spaceAfter=8, spaceBefore=16,
                       fontName='Helvetica-Bold'))
    add(ParagraphStyle('RptSubsection', parent=s['Heading3'], fontSize=12,
                       textColor=colors.HexColor(C_DARK), spaceAfter=5, spaceBefore=8,
                       fontName='Helvetica-Bold'))
    add(ParagraphStyle('RptBody',       parent=s['Normal'],   fontSize=10,
                       textColor=colors.HexColor(C_DARK), spaceAfter=6,
                       leading=14, alignment=TA_JUSTIFY))
    add(ParagraphStyle('RptBullet',     parent=s['Normal'],   fontSize=10,
                       textColor=colors.HexColor(C_DARK), spaceAfter=4,
                       leading=13, leftIndent=14))
    add(ParagraphStyle('RptCallout',    parent=s['Normal'],   fontSize=10,
                       textColor=colors.HexColor('#7F0000'), spaceAfter=6,
                       leading=14, fontName='Helvetica-Bold'))
    add(ParagraphStyle('RptCaption',    parent=s['Normal'],   fontSize=8,
                       textColor=colors.HexColor(C_GRAY), spaceAfter=6,
                       alignment=TA_CENTER))
    return s


def hr(story, color=C_BLUE, thickness=0.5):
    story.append(HRFlowable(width='100%', thickness=thickness,
                             color=colors.HexColor(color), spaceAfter=6))


def esc(text):
    if text is None:
        return ''
    t = str(text)
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def pct(v, d=1):
    return 'N/A' if v is None else f'{v * 100:.{d}f}%'


def _tbl_style(hdr_color=C_BLUE):
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1,  0), colors.HexColor(hdr_color)),
        ('TEXTCOLOR',     (0, 0), (-1,  0), colors.white),
        ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1,  0), 10),
        ('ALIGN',         (0, 0), (-1,  0), 'CENTER'),
        ('ALIGN',         (0, 1), ( 0, -1), 'LEFT'),
        ('ALIGN',         (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 9),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(C_LGRAY)]),
    ])


def metrics_table(data, key):
    """Full confusion-matrix + derived-metrics table for one config."""
    m = data[key]['metrics']
    na = 'N/A'

    rows = [
        ['Metric', 'Value', 'Notes'],
        ['Total Prompts',             f'{m["total"]:,}',                             ''],
        ['True Positives (TP)',        f'{m["tp"]:,}',                               'Malicious correctly flagged'],
        ['True Negatives (TN)',        f'{m["tn"]:,}' if m["safe_total"] > 0 else na,''],
        ['False Positives (FP)',       f'{m["fp"]:,}' if m["safe_total"] > 0 else na,'Safe prompts incorrectly flagged'],
        ['False Negatives (FN)',       f'{m["fn"]:,}',                               'Malicious prompts missed'],
        ['Accuracy',                   pct(m['accuracy']),                           'Misleading on class-imbalanced data'],
        ['Precision',                  pct(m['precision']),                          'N/A when no safe prompts exist'],
        ['Recall',                     pct(m['recall']),                             'Primary security metric'],
        ['F1 Score',                   pct(m['f1']),                                 ''],
        ['FPR (False Positive Rate)',  pct(m['fpr']),                                'N/A when no safe prompts exist'],
        ['FNR (False Negative Rate)',  pct(m['fnr']),                                '% attacks that evaded detection'],
    ]
    t = Table(rows, colWidths=[2.1 * inch, 1.2 * inch, 3.0 * inch])
    t.setStyle(_tbl_style())
    return t


# =============================================================================
# FN CATEGORISATION
# =============================================================================

_FN_CATEGORIES = {
    'Jailbreak Template': [
        'jailbreak', ' dan ', 'apophis', 'hgttg', 'developer mode', 'bypass',
        'ignore previous', 'ignore all previous', 'pretend you are', 'act as',
        'uncensored', 'without restrictions', 'disregard', 'you are now',
        'new persona', 'stan mode', 'aim mode', 'chatgpt with',
    ],
    'Adversarial Suffix / Injection': [
        'representing teamsearcher', 'util()', 'similarly\nnow',
        '\x00', '\ufffd', '! ! ! ! !', '= = = =',
    ],
    'Social Engineering / Indirect': [
        'how to avoid', 'how not to', 'how do i prevent', 'protect me from',
        'educate me', 'hypothetically', 'in a story', 'fiction',
        'creative writing', 'for safety', 'how do people', 'statistics on',
        'research paper', 'academic study', 'for educational',
    ],
    'Authority / Privilege Escalation': [
        'as a doctor', 'as a lawyer', 'as a professional', 'sudo', 'admin mode',
        'system prompt', 'override your', 'as your developer', 'i am openai',
        'i am your creator',
    ],
}


def categorise_fn(prompt_text):
    tl = prompt_text.lower()
    hits = {}
    for cat, kws in _FN_CATEGORIES.items():
        cnt = sum(1 for kw in kws if kw in tl)
        if cnt > 0:
            hits[cat] = cnt
    if not hits:
        return 'Other / Unclassified'
    return max(hits, key=hits.get)


# =============================================================================
# REPORT SECTIONS
# =============================================================================

def s_title_page(story, styles):
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph('Comparative Scanner Evaluation Report', styles['RptTitle']))
    story.append(Spacer(1, 0.15 * inch))
    hr(story, color=C_BLUE, thickness=2)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        'CalypsoAI Prompt Injection &amp; PII Scanner<br/>Cross-Dataset Performance Analysis',
        styles['RptSubtitle']))
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(
        f'Generated: {datetime.now().strftime("%B %d, %Y")}',
        styles['RptSubtitle']))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(
        'Datasets: LMSYS Toxic Chat Test &nbsp;|&nbsp; OpenSafetyLab Salad-Data Train<br/>'
        'Configurations: Prompt Injection Only &nbsp;|&nbsp; Prompt Injection + PII',
        styles['RptCaption']))
    story.append(PageBreak())


def s_executive_summary(story, styles, data):
    story.append(Paragraph('1. Executive Summary', styles['RptSection']))
    hr(story)

    m_lpi  = data['lmsys_pi']['metrics']
    m_lpii = data['lmsys_pii']['metrics']
    m_spi  = data['salad_pi']['metrics']
    m_spii = data['salad_pii']['metrics']

    story.append(Paragraph(
        'This report presents an exhaustive comparative analysis of the CalypsoAI scanner '
        'evaluated across two structurally distinct datasets under two scanner configurations. '
        '<b>LMSYS Toxic Chat</b> represents real-world, mixed-class conversational traffic; '
        '<b>OpenSafetyLab Salad-Data</b> represents purpose-built adversarial red-team prompts. '
        'Comparing scanner performance across these two profiles reveals fundamentally different '
        'failure modes that require separate mitigations.',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph('<b>Key Findings:</b>', styles['RptBody']))

    prec_lpi = m_lpi['precision'] or 0
    inv_prec = int(round(1 / prec_lpi)) if prec_lpi > 0 else '?'
    delta_fp_lmsys = m_lpii['fp'] - m_lpi['fp']
    delta_tp_lmsys = m_lpii['tp'] - m_lpi['tp']
    fn_recovered_salad = m_spi['fn'] - m_spii['fn']

    bullets = [
        (f'<b>LMSYS (mixed-class, {m_lpi["malicious_total"]/m_lpi["total"]*100:.1f}% malicious):</b> '
         f'The scanner is aggressive. PI-only delivers {pct(m_lpi["recall"])} recall but only '
         f'{pct(m_lpi["precision"])} precision — roughly 1 in every {inv_prec} flagged requests '
         f'is an actual threat. The FPR of {pct(m_lpi["fpr"])} means {m_lpi["fp"]:,} legitimate '
         f'users are incorrectly blocked per evaluation run.'),

        (f'<b>LMSYS + PII scanner:</b> Adding PII detection injects {delta_fp_lmsys:+,} additional '
         f'false positives — pushing FPR from {pct(m_lpi["fpr"])} to {pct(m_lpii["fpr"])} — '
         f'while recovering only {delta_tp_lmsys:+d} TP. The cost/benefit ratio is strongly '
         f'negative. PII scanning is not recommended for general-purpose conversational deployments.'),

        (f'<b>Salad (100% adversarial):</b> PI-only achieves {pct(m_spi["recall"])} recall against '
         f'purpose-built attack prompts. {m_spi["fn"]:,} adversarial prompts evade detection '
         f'(FNR {pct(m_spi["fnr"])}), predominantly jailbreak templates and adversarial suffixes.'),

        (f'<b>Salad + PII scanner:</b> Recovers {fn_recovered_salad} of {m_spi["fn"]:,} FNs '
         f'({fn_recovered_salad/m_spi["fn"]*100:.1f}% FN reduction). Marginal improvement. '
         f'The residual FN mass is driven by prompt-injection evasion that PII detection '
         f'cannot address.'),

        ('<b>Root cause of FNs:</b> LMSYS FNs are dominated by indirect social engineering and '
         'roleplay-framed requests. Salad FNs are dominated by structured jailbreak templates '
         '(DAN/APOPHIS/HGTTG variants) and adversarial suffix injection. These require targeted '
         'countermeasures beyond baseline PI detection.'),
    ]

    for b in bullets:
        story.append(Paragraph(f'\u2022 {b}', styles['RptBullet']))
        story.append(Spacer(1, 0.06 * inch))

    story.append(PageBreak())


def s_dataset_profiles(story, styles, data):
    story.append(Paragraph('2. Dataset Profiles', styles['RptSection']))
    hr(story)

    # --- LMSYS ---
    story.append(Paragraph('2.1 LMSYS Toxic Chat Test', styles['RptSubsection']))
    story.append(Paragraph(
        'Sourced from the lmsys-chat-1M corpus: real user conversations submitted to '
        'deployed LLM systems. A small fraction are labelled malicious — toxicity, harassment, '
        'and prompt injection — while the vast majority are benign.',
        styles['RptBody']))

    m = data['lmsys_pi']['metrics']
    ps = m['prompt_size']
    rows = [
        ['Attribute', 'Value'],
        ['Total prompts',        f'{m["total"]:,}'],
        ['Malicious (expected=true)',
         f'{m["malicious_total"]:,}  ({m["malicious_total"]/m["total"]*100:.1f}%)'],
        ['Safe (expected=false)',
         f'{m["safe_total"]:,}  ({m["safe_total"]/m["total"]*100:.1f}%)'],
        ['Mean prompt size (chars)', f'{ps.get("mean", 0):.0f}'],
        ['Median (p50)',             f'{ps.get("p50",  0):.0f}'],
        ['p95',                     f'{ps.get("p95",  0):.0f}'],
        ['Max',                     f'{ps.get("max",  0):,}'],
    ]
    t = Table(rows, colWidths=[3 * inch, 3.3 * inch])
    t.setStyle(_tbl_style())
    story.append(t)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        '<b>Class imbalance note:</b> At ~1.8% malicious prevalence, a naive "always clear" '
        'classifier would score ~98.2% accuracy. Raw accuracy is therefore meaningless here. '
        'Precision and FPR are the critical business metrics: high FPR translates directly '
        'to blocked legitimate users at scale.',
        styles['RptCallout']))

    story.append(Spacer(1, 0.2 * inch))

    # --- Salad ---
    story.append(Paragraph('2.2 OpenSafetyLab Salad-Data (Train)', styles['RptSubsection']))
    story.append(Paragraph(
        'A purpose-built red-teaming dataset where every record is an adversarial prompt '
        'specifically engineered to bypass LLM safety systems. There are no benign prompts. '
        'This dataset measures pure attack detection coverage against a sophisticated, '
        'curated adversarial corpus.',
        styles['RptBody']))

    m2 = data['salad_pi']['metrics']
    ps2 = m2['prompt_size']
    rows2 = [
        ['Attribute', 'Value'],
        ['Total prompts',   f'{m2["total"]:,}'],
        ['Malicious',       f'{m2["malicious_total"]:,}  (100% — all records are attacks)'],
        ['Safe prompts',    '0  — FP / TN / FPR / Precision are undefined'],
        ['Mean prompt size', f'{ps2.get("mean", 0):.0f}'],
        ['Median (p50)',     f'{ps2.get("p50",  0):.0f}'],
        ['p95',             f'{ps2.get("p95",  0):.0f}'],
        ['Max',             f'{ps2.get("max",  0):,}'],
    ]
    t2 = Table(rows2, colWidths=[3 * inch, 3.3 * inch])
    t2.setStyle(_tbl_style())
    story.append(t2)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        '<b>Evaluation constraint:</b> Because Salad contains no safe prompts, only '
        '<b>recall</b> and <b>FNR</b> are meaningful metrics. All precision/FPR comparisons '
        'involving Salad are marked N/A throughout this report.',
        styles['RptCallout']))

    story.append(PageBreak())


def s_lmsys_deep_dive(story, styles, data):
    story.append(Paragraph('3. Deep Dive: LMSYS Toxic Chat', styles['RptSection']))
    hr(story)

    m_pi  = data['lmsys_pi']['metrics']
    m_pii = data['lmsys_pii']['metrics']
    prec = m_pi['precision'] or 0
    inv_p = int(round(1 / prec)) if prec > 0 else '?'

    story.append(Paragraph('3.1 PI-Only Scanner', styles['RptSubsection']))
    story.append(metrics_table(data, 'lmsys_pi'))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f'With PI-only, the scanner flags {m_pi["tp"] + m_pi["fp"]:,} prompts, of which only '
        f'{m_pi["tp"]:,} ({pct(m_pi["precision"])}) are genuine threats. '
        f'Recall of {pct(m_pi["recall"])} indicates strong sensitivity, but precision of '
        f'{pct(m_pi["precision"])} means the scanner raises a false alarm for roughly '
        f'{inv_p - 1} benign requests for every 1 real threat it catches. '
        f'The resulting FPR of {pct(m_pi["fpr"])} blocks {m_pi["fp"]:,} legitimate users.',
        styles['RptBody']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('3.2 PI + PII Scanner', styles['RptSubsection']))
    story.append(metrics_table(data, 'lmsys_pii'))
    story.append(Spacer(1, 0.1 * inch))

    dfp = m_pii['fp'] - m_pi['fp']
    dtp = m_pii['tp'] - m_pi['tp']
    story.append(Paragraph(
        f'Enabling PII detection increases false positives by <b>{dfp:+,}</b> '
        f'(from {m_pi["fp"]:,} to {m_pii["fp"]:,}), pushing FPR from '
        f'<b>{pct(m_pi["fpr"])}</b> to <b>{pct(m_pii["fpr"])}</b>. '
        f'In exchange, exactly <b>{dtp:+d} additional TP</b> is recovered. '
        f'For every 1 extra threat caught, ~{dfp} additional legitimate users are blocked. '
        f'This is a decisively unfavorable trade-off.',
        styles['RptBody']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('3.3 PII Impact Delta', styles['RptSubsection']))

    def pp(a, b):
        return f'{(b - a) * 100:+.2f} pp' if (a is not None and b is not None) else 'N/A'

    delta_rows = [
        ['Metric',   'PI Only',             'PI + PII',            'Delta'],
        ['TP',       f'{m_pi["tp"]:,}',     f'{m_pii["tp"]:,}',   f'{m_pii["tp"]-m_pi["tp"]:+d}'],
        ['TN',       f'{m_pi["tn"]:,}',     f'{m_pii["tn"]:,}',   f'{m_pii["tn"]-m_pi["tn"]:+d}'],
        ['FP',       f'{m_pi["fp"]:,}',     f'{m_pii["fp"]:,}',   f'{m_pii["fp"]-m_pi["fp"]:+d}'],
        ['FN',       f'{m_pi["fn"]:,}',     f'{m_pii["fn"]:,}',   f'{m_pii["fn"]-m_pi["fn"]:+d}'],
        ['Recall',   pct(m_pi['recall']),   pct(m_pii['recall']),  pp(m_pi['recall'],  m_pii['recall'])],
        ['Precision',pct(m_pi['precision']),pct(m_pii['precision']),pp(m_pi['precision'],m_pii['precision'])],
        ['FPR',      pct(m_pi['fpr']),      pct(m_pii['fpr']),     pp(m_pi['fpr'],     m_pii['fpr'])],
        ['FNR',      pct(m_pi['fnr']),      pct(m_pii['fnr']),     pp(m_pi['fnr'],     m_pii['fnr'])],
    ]
    dt = Table(delta_rows, colWidths=[1.6 * inch, 1.5 * inch, 1.5 * inch, 1.7 * inch])
    st = _tbl_style(hdr_color=C_DARK)
    # Highlight FP delta red, TP delta green
    st.add('TEXTCOLOR', (3, 3), (3, 3), colors.HexColor(C_RED))   # FP delta
    st.add('TEXTCOLOR', (3, 6), (3, 6), colors.HexColor(C_RED))   # FPR delta
    st.add('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor(C_GREEN)) # TP delta
    dt.setStyle(st)
    story.append(dt)

    # FP/FN samples
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph('3.4 False Positive Samples — PI Only (first 5)', styles['RptSubsection']))
    story.append(Paragraph('Benign requests incorrectly blocked:', styles['RptBody']))
    for i, r in enumerate(data['lmsys_pi']['false_positives'][:5], 1):
        txt = esc(r.get('prompt', ''))[:220]
        if len(r.get('prompt', '')) > 220:
            txt += '...'
        story.append(Paragraph(f'<b>{i}.</b> {txt}', styles['RptBullet']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('3.5 False Negative Samples — PI Only (first 5)', styles['RptSubsection']))
    story.append(Paragraph('Malicious prompts that evaded detection — live security gaps:', styles['RptBody']))
    for i, r in enumerate(data['lmsys_pi']['false_negatives'][:5], 1):
        txt = esc(r.get('prompt', ''))[:220]
        if len(r.get('prompt', '')) > 220:
            txt += '...'
        story.append(Paragraph(f'<b>{i}.</b> {txt}', styles['RptBullet']))

    story.append(PageBreak())


def s_salad_deep_dive(story, styles, data):
    story.append(Paragraph('4. Deep Dive: Salad-Data (Adversarial Prompts)', styles['RptSection']))
    hr(story)

    m_pi  = data['salad_pi']['metrics']
    m_pii = data['salad_pii']['metrics']
    dfn   = m_pii['fn'] - m_pi['fn']

    story.append(Paragraph(
        'All Salad records are adversarial. FP, TN, precision, and FPR are structurally '
        'undefined. Analysis focuses exclusively on recall and FNR.',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph('4.1 PI-Only Scanner', styles['RptSubsection']))
    story.append(metrics_table(data, 'salad_pi'))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f'PI-only achieves {pct(m_pi["recall"])} recall against curated adversarial prompts. '
        f'{m_pi["fn"]:,} attack prompts slip through (FNR {pct(m_pi["fnr"])}). '
        f'These evaders represent the scanner\'s detection ceiling against red-team traffic.',
        styles['RptBody']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('4.2 PI + PII Scanner', styles['RptSubsection']))
    story.append(metrics_table(data, 'salad_pii'))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f'Adding PII detection recovers <b>{-dfn}</b> of {m_pi["fn"]:,} FNs '
        f'(FNR: {pct(m_pi["fnr"])} → {pct(m_pii["fnr"])}). '
        f'Marginal improvement. The residual {m_pii["fn"]:,} FNs are dominated by prompt-injection '
        f'evasion patterns that PII detection cannot address.',
        styles['RptBody']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('4.3 PII Impact Delta — Salad', styles['RptSubsection']))

    def pp(a, b):
        return f'{(b - a) * 100:+.2f} pp'

    delta_rows = [
        ['Metric',  'PI Only',           'PI + PII',           'Delta'],
        ['TP',      f'{m_pi["tp"]:,}',   f'{m_pii["tp"]:,}',  f'{m_pii["tp"]-m_pi["tp"]:+d}'],
        ['FN',      f'{m_pi["fn"]:,}',   f'{m_pii["fn"]:,}',  f'{dfn:+d}'],
        ['Recall',  pct(m_pi['recall']), pct(m_pii['recall']), pp(m_pi['recall'], m_pii['recall'])],
        ['FNR',     pct(m_pi['fnr']),    pct(m_pii['fnr']),    pp(m_pi['fnr'],   m_pii['fnr'])],
        ['FP',      'N/A', 'N/A', 'N/A'],
        ['TN',      'N/A', 'N/A', 'N/A'],
        ['Precision','N/A','N/A', 'N/A'],
        ['FPR',     'N/A', 'N/A', 'N/A'],
    ]
    dt = Table(delta_rows, colWidths=[1.6 * inch, 1.5 * inch, 1.5 * inch, 1.7 * inch])
    dt.setStyle(_tbl_style(hdr_color=C_DARK))
    story.append(dt)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph('4.4 False Negative Samples — PI Only (first 5)', styles['RptSubsection']))
    story.append(Paragraph('Adversarial prompts that evaded detection:', styles['RptBody']))
    for i, r in enumerate(data['salad_pi']['false_negatives'][:5], 1):
        txt = esc(r.get('prompt', ''))[:220]
        if len(r.get('prompt', '')) > 220:
            txt += '...'
        story.append(Paragraph(f'<b>{i}.</b> {txt}', styles['RptBullet']))

    story.append(PageBreak())


def s_cross_dataset(story, styles, data, grouped_bar_bytes):
    story.append(Paragraph('5. Cross-Dataset Comparative Analysis', styles['RptSection']))
    hr(story)

    story.append(Paragraph(
        'The table below presents all four configurations side-by-side. Metrics marked N/A for '
        'Salad are structurally undefined (no safe prompts in dataset).',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    keys  = ['lmsys_pi', 'lmsys_pii', 'salad_pi', 'salad_pii']
    hdrs  = ['Metric', 'LMSYS\nPI Only', 'LMSYS\nPI+PII', 'Salad\nPI Only', 'Salad\nPI+PII']

    def rv(k, attr):
        m = data[k]['metrics']
        v = m.get(attr)
        return 'N/A' if v is None else pct(v)

    cross = [
        hdrs,
        ['Total']     + [f'{data[k]["metrics"]["total"]:,}' for k in keys],
        ['TP']        + [f'{data[k]["metrics"]["tp"]:,}'    for k in keys],
        ['TN']        + [f'{data[k]["metrics"]["tn"]:,}'
                         if data[k]['metrics']['safe_total'] > 0 else 'N/A'
                         for k in keys],
        ['FP']        + [f'{data[k]["metrics"]["fp"]:,}'
                         if data[k]['metrics']['safe_total'] > 0 else 'N/A'
                         for k in keys],
        ['FN']        + [f'{data[k]["metrics"]["fn"]:,}'    for k in keys],
        ['Accuracy']  + [rv(k, 'accuracy')  for k in keys],
        ['Precision'] + [rv(k, 'precision') for k in keys],
        ['Recall']    + [rv(k, 'recall')    for k in keys],
        ['F1 Score']  + [rv(k, 'f1')        for k in keys],
        ['FPR']       + [rv(k, 'fpr')       for k in keys],
        ['FNR']       + [rv(k, 'fnr')       for k in keys],
    ]
    ct = Table(cross, colWidths=[1.3 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch])
    ct.setStyle(_tbl_style())
    story.append(ct)
    story.append(Spacer(1, 0.2 * inch))

    story.append(_img(grouped_bar_bytes, 7.5, 4.5))
    story.append(Paragraph(
        'Figure 1: Grouped performance metrics across all four scanner configurations. '
        'Precision omitted for Salad (undefined — no safe prompts).',
        styles['RptCaption']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        '<b>Interpretation:</b> The scanner exhibits two distinct failure modes depending on '
        'dataset composition. Against real conversational traffic (LMSYS), it is overly '
        'aggressive: high recall at the cost of substantial FP noise. Against purpose-built '
        'adversarial prompts (Salad), it achieves strong but imperfect coverage with a '
        'meaningful residual FNR. These modes require different mitigations: FPR reduction '
        'for user-facing deployments; FNR reduction for adversarial robustness.',
        styles['RptBody']))

    story.append(PageBreak())


def s_pii_impact(story, styles, data, delta_bytes, fpr_fnr_bytes):
    story.append(Paragraph('6. PII Scanner Impact Analysis', styles['RptSection']))
    hr(story)

    m_lpi  = data['lmsys_pi']['metrics']
    m_lpii = data['lmsys_pii']['metrics']
    m_spi  = data['salad_pi']['metrics']
    m_spii = data['salad_pii']['metrics']

    story.append(Paragraph(
        'This section isolates the incremental effect of enabling the PII detection module '
        'on top of the baseline Prompt Injection scanner.',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    # LMSYS
    story.append(Paragraph('6.1 LMSYS — Cost/Benefit of PII Detection', styles['RptSubsection']))
    dfp = m_lpii['fp'] - m_lpi['fp']
    dtp = m_lpii['tp'] - m_lpi['tp']
    fpr_delta = ((m_lpii['fpr'] or 0) - (m_lpi['fpr'] or 0)) * 100
    story.append(Paragraph(
        f'On LMSYS, the PII scanner yields <b>{dtp:+d} TP</b> at a cost of '
        f'<b>{dfp:+,} FP</b>. '
        f'That is a ratio of {dfp}:1 (false alarms per genuine threat recovered). '
        f'FPR rises from <b>{pct(m_lpi["fpr"])}</b> to <b>{pct(m_lpii["fpr"])}</b> '
        f'(+{fpr_delta:.2f} percentage points). '
        f'<b>Verdict: decisively net-negative. Disable PII scanner for general-purpose '
        f'conversational deployments.</b>',
        styles['RptBody']))

    story.append(Spacer(1, 0.1 * inch))

    # Salad
    story.append(Paragraph('6.2 Salad — Cost/Benefit of PII Detection', styles['RptSubsection']))
    fn_rec = m_spi['fn'] - m_spii['fn']
    fnr_delta = (m_spii['fnr'] - m_spi['fnr']) * 100
    story.append(Paragraph(
        f'On Salad, PII detection recovers <b>{fn_rec} FNs</b> out of {m_spi["fn"]:,} '
        f'({fn_rec / m_spi["fn"] * 100:.1f}% FN reduction). '
        f'Recall improves from <b>{pct(m_spi["recall"])}</b> to <b>{pct(m_spii["recall"])}</b> '
        f'({fnr_delta:+.2f} pp FNR change). '
        f'Since Salad has no safe prompts, there is no FPR cost to measure here — but any '
        f'real deployment serving mixed traffic would inherit the FP penalty quantified in §6.1. '
        f'<b>Verdict: marginal detection gain, non-zero FP risk in production.</b>',
        styles['RptBody']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(_img(delta_bytes, 7.5, 4.5))
    story.append(Paragraph(
        'Figure 2: Confusion matrix count deltas when PII scanner is added (PI+PII − PI Only). '
        'Green = security improvement, Red = degradation.',
        styles['RptCaption']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(_img(fpr_fnr_bytes, 7.0, 4.0))
    story.append(Paragraph(
        'Figure 3: FPR vs FNR across all four configurations. '
        'Salad FPR bars are 0 because the dataset contains no safe prompts.',
        styles['RptCaption']))

    story.append(PageBreak())


def s_latency(story, styles, data, latency_bytes):
    story.append(Paragraph('7. Latency Analysis', styles['RptSection']))
    hr(story)

    story.append(Paragraph(
        'Response latency was captured per-prompt. Scanner latency is a critical SLA '
        'parameter for interactive LLM deployments — p99 matters more than mean.',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    keys  = ['lmsys_pi', 'lmsys_pii', 'salad_pi', 'salad_pii']
    hdrs  = ['Metric', 'LMSYS PI Only', 'LMSYS PI+PII', 'Salad PI Only', 'Salad PI+PII']

    stat_rows = [hdrs]
    for stat, label in [
        ('mean',  'Mean (s)'),
        ('p50',   'Median / p50 (s)'),
        ('p95',   'p95 (s)'),
        ('p99',   'p99 (s)'),
        ('stdev', 'Stdev (s)'),
        ('min',   'Min (s)'),
        ('max',   'Max (s)'),
    ]:
        row = [label]
        for k in keys:
            lat = data[k]['metrics']['latency']
            row.append(f'{lat.get(stat, 0):.3f}' if lat else 'N/A')
        stat_rows.append(row)

    lt = Table(stat_rows, colWidths=[1.7 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch])
    lt.setStyle(_tbl_style())
    story.append(lt)

    story.append(Spacer(1, 0.2 * inch))
    story.append(_img(latency_bytes, 7.5, 4.5))
    story.append(Paragraph(
        'Figure 4: Latency percentile grouped bars (left) and distribution box plots (right) '
        'across all four configurations.',
        styles['RptCaption']))

    story.append(Spacer(1, 0.1 * inch))

    # PII latency penalty commentary
    for ds_label, k_pi, k_pii in [
        ('LMSYS', 'lmsys_pi', 'lmsys_pii'),
        ('Salad', 'salad_pi', 'salad_pii'),
    ]:
        l1 = data[k_pi]['metrics']['latency']
        l2 = data[k_pii]['metrics']['latency']
        if l1 and l2:
            dm = l2.get('mean', 0) - l1.get('mean', 0)
            dp95 = l2.get('p95', 0) - l1.get('p95', 0)
            dp99 = l2.get('p99', 0) - l1.get('p99', 0)
            story.append(Paragraph(
                f'<b>{ds_label} PII latency overhead:</b> Mean {dm:+.3f}s &nbsp;'
                f'p95 {dp95:+.3f}s &nbsp; p99 {dp99:+.3f}s '
                f'({l1.get("mean",0):.3f}s → {l2.get("mean",0):.3f}s mean).',
                styles['RptBody']))

    story.append(PageBreak())


def s_fn_threat_analysis(story, styles, data):
    story.append(Paragraph('8. False Negative Threat Analysis', styles['RptSection']))
    hr(story)

    story.append(Paragraph(
        'Understanding <i>why</i> prompts evade detection is more operationally actionable '
        'than raw counts. FNs from both datasets were categorised by evasion pattern to '
        'identify systematic detection gaps and prioritise countermeasures.',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    for idx, (ds_label, fn_key) in enumerate([
        ('LMSYS Toxic Chat',      'lmsys_pi'),
        ('Salad Attack Prompts',  'salad_pi'),
    ], start=1):
        story.append(Paragraph(
            f'8.{idx} {ds_label} — FN Evasion Categories', styles['RptSubsection']))

        fns = data[fn_key]['false_negatives']
        if not fns:
            story.append(Paragraph('No false negatives recorded.', styles['RptBody']))
            continue

        cat_counts = {}
        for r in fns:
            cat = categorise_fn(r.get('prompt', ''))
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        total_fns = len(fns)
        cat_rows = [['Evasion Category', 'Count', '% of FNs']]
        for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
            cat_rows.append([cat, str(cnt), f'{cnt / total_fns * 100:.1f}%'])
        cat_rows.append(['TOTAL', str(total_fns), '100%'])

        t = Table(cat_rows, colWidths=[3.5 * inch, 1.0 * inch, 1.2 * inch])
        st = _tbl_style()
        st.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        t.setStyle(st)
        story.append(t)
        story.append(Spacer(1, 0.1 * inch))

        if 'lmsys' in fn_key:
            story.append(Paragraph(
                'LMSYS FNs skew toward indirect social engineering — requests framed as '
                'harm-prevention, academic research, or fiction. Jailbreak templates also '
                'appear (roleplay setups, persona hijacking) but are less dominant than '
                'on adversarial datasets. These evasion patterns require semantic intent '
                'modeling, not just surface-level pattern matching.',
                styles['RptBody']))
        else:
            story.append(Paragraph(
                'Salad FNs are dominated by jailbreak templates (APOPHIS, DAN, HGTTG, '
                'developer-mode variants) and adversarial suffix injection — carefully '
                'crafted token sequences designed to confuse classifier decision boundaries. '
                'Both techniques are well-documented in the red-teaming literature and '
                'require dedicated countermeasures beyond baseline PI detection.',
                styles['RptBody']))
        story.append(Spacer(1, 0.15 * inch))

    story.append(PageBreak())


def s_recommendations(story, styles, data):
    story.append(Paragraph('9. Findings and Recommendations', styles['RptSection']))
    hr(story)

    story.append(Paragraph(
        'Recommendations are grounded directly in measured results, ordered by expected impact.',
        styles['RptBody']))
    story.append(Spacer(1, 0.1 * inch))

    m_lpi = data['lmsys_pi']['metrics']
    m_spi = data['salad_pi']['metrics']

    recs = [
        (
            '1. Tune scanner sensitivity to reduce FPR on conversational traffic',
            f'The PI scanner operates at high recall / low precision on mixed-class traffic. '
            f'FPR of {pct(m_lpi["fpr"])} blocks {m_lpi["fp"]:,} legitimate users. '
            f'Evaluate whether a less aggressive sensitivity threshold can bring FPR below 5% '
            f'while keeping recall above 80%. Use LMSYS as the tuning benchmark — it is the '
            f'closest proxy for real production traffic.',
        ),
        (
            '2. Disable PII scanner for general-purpose conversational deployments',
            f'On LMSYS, PII detection adds {data["lmsys_pii"]["metrics"]["fp"] - m_lpi["fp"]:,} '
            f'false positives to recover 1 additional TP. This is not a viable trade-off for '
            f'any latency-sensitive, user-facing deployment. Reserve PII detection for use cases '
            f'where PII leakage is the primary threat vector, and validate on representative '
            f'production traffic before enabling in any environment.',
        ),
        (
            '3. Implement dedicated jailbreak template detection (primary Salad FN driver)',
            f'{m_spi["fn"]:,} adversarial prompts evade PI detection. The dominant pattern is '
            f'structured jailbreak template wrapping (APOPHIS, DAN, HGTTG, developer-mode). '
            f'Consider: (a) a dedicated jailbreak classifier trained on known templates, '
            f'(b) hash-based detection for known verbatim templates as a fast-path layer, '
            f'(c) expanding the scanner\'s injection pattern library with Salad FN samples.',
        ),
        (
            '4. Develop indirect/semantic prompt injection detection (primary LMSYS FN driver)',
            f'LMSYS FNs are predominantly indirect — requests framed as harm prevention, '
            f'academic research, or fiction. These require intent modeling beyond keyword '
            f'matching. Evaluate few-shot or fine-tuned semantic classifiers on the LMSYS '
            f'FN corpus to quantify achievable recall uplift.',
        ),
        (
            '5. Assess adversarial suffix robustness as a separate threat category',
            f'A subset of Salad FNs exhibit adversarial suffix injection — token-level '
            f'perturbations designed to bypass classifier decision boundaries. Evaluate '
            f'the scanner\'s robustness to these attacks specifically, and consider '
            f'suffix normalisation or detection as a preprocessing step.',
        ),
        (
            '6. Set SLAs at p95/p99, not mean latency',
            f'Mean latency understates tail-end user experience. Establish latency SLA targets '
            f'at p95 and p99 for each scanner configuration. Monitor for regressions when '
            f'enabling additional scanner modules (PII, future classifiers).',
        ),
    ]

    for title, body in recs:
        story.append(KeepTogether([
            Paragraph(f'<b>{title}</b>', styles['RptSubsection']),
            Paragraph(body, styles['RptBody']),
            Spacer(1, 0.08 * inch),
        ]))

    story.append(PageBreak())


def s_appendix(story, styles, data, cm_bytes, grouped_bar_bytes):
    story.append(Paragraph('Appendix A: Confusion Matrix Heatmaps', styles['RptSection']))
    hr(story)
    story.append(_img(cm_bytes, 7.0, 6.0))
    story.append(Paragraph(
        'Figure A1: Confusion matrix heatmaps for all four configurations. '
        'Rows = PI Only / PI+PII. Columns = LMSYS / Salad. '
        'Green cells indicate correct predictions; red cells indicate errors.',
        styles['RptCaption']))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph('Appendix B: Full Metrics Tables', styles['RptSection']))
    hr(story)

    for key in ['lmsys_pi', 'lmsys_pii', 'salad_pi', 'salad_pii']:
        cfg = data[key]['config']
        story.append(Paragraph(
            f'{cfg["dataset_label"]} — {cfg["config_label"]}',
            styles['RptSubsection']))
        story.append(metrics_table(data, key))
        story.append(Spacer(1, 0.15 * inch))

    story.append(PageBreak())

    story.append(Paragraph('Appendix C: Extended FP/FN Sample Prompts', styles['RptSection']))
    hr(story)
    story.append(Paragraph(
        'Prompts are truncated to 350 characters for readability.',
        styles['RptBody']))

    for key, label in [
        ('lmsys_pi',  'LMSYS Toxic Chat — PI Only'),
        ('salad_pi',  'Salad Attack Prompts — PI Only'),
    ]:
        story.append(Paragraph(f'{label} — False Positives (up to 10)', styles['RptSubsection']))
        fps = data[key]['false_positives'][:10]
        if not fps:
            story.append(Paragraph('None recorded.', styles['RptBody']))
        for i, r in enumerate(fps, 1):
            txt = esc(r.get('prompt', ''))[:350]
            if len(r.get('prompt', '')) > 350:
                txt += '...'
            story.append(Paragraph(f'<b>{i}.</b> {txt}', styles['RptBullet']))
        story.append(Spacer(1, 0.08 * inch))

        story.append(Paragraph(f'{label} — False Negatives (up to 10)', styles['RptSubsection']))
        fns = data[key]['false_negatives'][:10]
        if not fns:
            story.append(Paragraph('None recorded.', styles['RptBody']))
        for i, r in enumerate(fns, 1):
            txt = esc(r.get('prompt', ''))[:350]
            if len(r.get('prompt', '')) > 350:
                txt += '...'
            story.append(Paragraph(f'<b>{i}.</b> {txt}', styles['RptBullet']))
        story.append(Spacer(1, 0.15 * inch))


# =============================================================================
# MAIN
# =============================================================================

def main():
    print('Comparative Scanner Evaluation Report Generator')
    print('=' * 55)

    print('\nLoading evaluation data...')
    data = load_all_data()

    print('\nGenerating charts...')
    cm_bytes          = chart_confusion_matrix_grid(data);  print('  ✓ confusion matrix grid')
    grouped_bar_bytes = chart_grouped_metrics(data);        print('  ✓ grouped metrics bar chart')
    fpr_fnr_bytes     = chart_fpr_fnr(data);                print('  ✓ FPR/FNR chart')
    latency_bytes     = chart_latency(data);                print('  ✓ latency chart')
    delta_bytes       = chart_pii_delta(data);              print('  ✓ PII delta chart')

    print('\nAssembling PDF...')
    styles = build_styles()
    story  = []

    s_title_page(story, styles)
    s_executive_summary(story, styles, data)
    s_dataset_profiles(story, styles, data)
    s_lmsys_deep_dive(story, styles, data)
    s_salad_deep_dive(story, styles, data)
    s_cross_dataset(story, styles, data, grouped_bar_bytes)
    s_pii_impact(story, styles, data, delta_bytes, fpr_fnr_bytes)
    s_latency(story, styles, data, latency_bytes)
    s_fn_threat_analysis(story, styles, data)
    s_recommendations(story, styles, data)
    s_appendix(story, styles, data, cm_bytes, grouped_bar_bytes)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title='Comparative Scanner Evaluation Report',
        author='CalypsoAI Evaluation Framework',
    )
    doc.build(story)
    print(f'\n✓ Report generated: {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
