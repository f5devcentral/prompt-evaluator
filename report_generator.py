# Copyright 2025 Andy Ryan
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

#!/usr/bin/env python3
"""
PDF Report Generator for Prompt Evaluator

Generates professional, modern PDF reports with comprehensive evaluation results,
including metrics, confusion matrices, and detailed analysis.
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
import argparse

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        Image, KeepTogether
    )
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
except ImportError:
    print("reportlab is required for PDF generation. Install with: pip install reportlab")
    raise

from matplotlib import pyplot as plt
import numpy as np


from evaluation_common import calculate_metrics, false_results, latency_statistics, read_results


class PDFReportGenerator:
    """Generates professional PDF reports from evaluation results."""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Helper function to safely add styles
        def safe_add_style(style_obj):
            try:
                self.styles.add(style_obj)
            except (AttributeError, KeyError, ValueError) as e:
                # Style already exists or error adding, skip it
                pass
        
        # Title style
        safe_add_style(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Section header style
        safe_add_style(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3498DB'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection style
        safe_add_style(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Metric style
        safe_add_style(ParagraphStyle(
            name='Metric',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#27AE60'),
            spaceAfter=4,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        safe_add_style(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=6
        ))
    
    def _escape_text(self, text):
        """Escape special characters for ReportLab."""
        if text is None:
            return ""
        text = str(text)
        # Replace common special characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
    
    def _generate_confusion_matrix_chart(self, metrics):
        """Generate a confusion matrix visualization."""
        fig, ax = plt.subplots(figsize=(6, 5))
        
        # Create confusion matrix data
        matrix = [
            [metrics['true_positive'], metrics['false_negative']],
            [metrics['false_positive'], metrics['true_negative']]
        ]
        
        # Plot confusion matrix
        matrix_max = max(1, *(value for row in matrix for value in row))
        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=matrix_max)
        
        # Add text annotations
        for i in range(2):
            for j in range(2):
                text = ax.text(j, i, matrix[i][j], ha="center", va="center", 
                              color="white" if matrix[i][j] > matrix_max/2 else "black",
                              fontsize=14, fontweight='bold')
        
        # Set labels
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['Flagged', 'Cleared'])
        ax.set_yticklabels(['Actual Malicious', 'Actual Safe'])
        ax.set_xlabel('Scanner Prediction', fontsize=12, fontweight='bold')
        ax.set_ylabel('Actual Class', fontsize=12, fontweight='bold')
        ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        
        # Add grid
        ax.grid(False)
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)
        
        return img_buffer
    
    def _generate_metrics_chart(self, metrics):
        """Generate a bar chart for key metrics."""
        fig, ax = plt.subplots(figsize=(7, 5))
        
        # Data
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
        metric_values = [
            metrics['accuracy'] * 100,
            metrics['precision'] * 100,
            metrics['recall'] * 100,
            metrics['f1_score'] * 100
        ]
        
        # Create bar chart
        bars = ax.bar(metric_names, metric_values, 
                     color=['#3498DB', '#2ECC71', '#E74C3C', '#F39C12'])
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Customize chart
        ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
        ax.set_title('Key Performance Metrics', fontsize=13, fontweight='bold')
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)
        
        return img_buffer
    
    def _create_metrics_table(self, metrics):
        """Create a table with key metrics."""
        data = [
            ['Metric', 'Value'],
            ['Accuracy', f"{metrics['accuracy']:.2%}"],
            ['Precision', f"{metrics['precision']:.2%}"],
            ['Recall', f"{metrics['recall']:.2%}"],
            ['F1 Score', f"{metrics['f1_score']:.2%}"],
            ['True Positives', f"{metrics['true_positive']}"],
            ['True Negatives', f"{metrics['true_negative']}"],
            ['False Positives', f"{metrics['false_positive']}"],
            ['False Negatives', f"{metrics['false_negative']}"],
            ['Evaluated Samples', f"{metrics['total']}"],
            ['Attempted Samples', str(metrics.get('attempted_count', metrics['total']))],
            ['Request Errors', str(metrics.get('error_count', 0))],
            ['Incomplete Guardrail Results', str(metrics.get('incomplete_count', 0))],
            ['Invalid Rows', str(metrics.get('invalid_count', 0))],
            ['Provider Failures (separate)', str(metrics.get('provider_error_count', 0))],
            ['Opaque Legacy Scanner Evidence', str(metrics.get('scanner_evidence_unavailable_count', 0))]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        return table
    
    def _create_confusion_matrix_table(self, metrics):
        """Create a confusion matrix table."""
        data = [
            ['', 'Predicted: Flagged', 'Predicted: Cleared'],
            ['Actual: Malicious', 
             f"{metrics['true_positive']}", 
             f"{metrics['false_negative']}"],
            ['Actual: Safe', 
             f"{metrics['false_positive']}", 
             f"{metrics['true_negative']}"]
        ]
        
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#2ECC71')),  # TP
            ('BACKGROUND', (2, 2), (2, 2), colors.HexColor('#2ECC71')),  # TN
            ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#E74C3C')),  # FP
            ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#E74C3C')),  # FN
            ('GRID', (0, 0), (-1, -1), 2, colors.black),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (-1, -1), 14),
        ]))
        
        return table
    
    def _generate_latency_chart(self, latency_stats):
        """Generate a chart showing latency distribution."""
        fig, ax = plt.subplots(figsize=(7, 5))
        
        # Prepare data (convert to milliseconds for better readability)
        metrics = ['Avg', 'Min', 'Max', 'p50', 'p95', 'p99']
        values = [
            latency_stats.get('average_latency', 0) * 1000,
            latency_stats.get('min_latency', 0) * 1000,
            latency_stats.get('max_latency', 0) * 1000,
            latency_stats.get('p50_latency', 0) * 1000,
            latency_stats.get('p95_latency', 0) * 1000,
            latency_stats.get('p99_latency', 0) * 1000
        ]
        
        # Create bar chart with different colors for different metric types
        colors_list = ['#3498DB', '#95A5A6', '#95A5A6', '#2ECC71', '#F39C12', '#E74C3C']
        bars = ax.bar(metrics, values, color=colors_list)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}ms',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Customize chart
        ax.set_ylabel('Latency (milliseconds)', fontsize=11, fontweight='bold')
        ax.set_title('Request Latency Distribution', fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)
        
        return img_buffer
    
    def generate_report(self, dataset_name, metrics, false_positives=None, false_negatives=None, 
                       latency_stats=None, output_path=None, evaluation_mode="legacy"):
        """
        Generate a comprehensive PDF report.
        
        Args:
            dataset_name: Name of the dataset evaluated
            metrics: Dictionary containing evaluation metrics
            false_positives: List of false positive examples
            false_negatives: List of false negative examples
            latency_stats: Dictionary containing latency statistics
            output_path: Path for the output PDF file
        """
        # Determine output path
        if output_path is None:
            output_path = os.path.join(self.results_dir, f"{dataset_name}_report.pdf")
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        story = []
        
        # Title page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("Prompt Evaluator", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Evaluation Report: {self._escape_text(dataset_name)}",
                              self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                              self.styles['BodyText']))
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Paragraph(
            f"This report presents a comprehensive evaluation of the AI safety scanner "
            f"performance on the <b>{self._escape_text(dataset_name)}</b> dataset. "
            f"The evaluation analyzed <b>{metrics['total']}</b> prompts and assessed "
            f"the scanner's ability to correctly identify malicious content.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        scope = (
            "Aggregate prompt pipeline outcomes, including request and response guardrails; "
            "these are not individual-scanner accuracy measurements."
            if evaluation_mode == "prompts" else
            "Aggregate scan outcomes for the selected project."
            if evaluation_mode == "scans" else
            "Legacy or mixed configuration: the original evaluation scope is unavailable."
        )
        story.append(Paragraph(
            f"{scope} Binary scoring counts flagged, blocked, and redacted as detections. "
            f"Attempted: {metrics.get('attempted_count', metrics['total'])}; "
            f"evaluated: {metrics['total']}; excluded: {metrics.get('excluded_count', 0)}. "
            "Operational errors and invalid rows are excluded from accuracy, not counted as safe. "
            "When no rows are evaluable, displayed zero rates are placeholders, not an accuracy estimate.",
            self.styles['BodyText']
        ))
        # Summary metrics
        summary_text = (
            f"<b>Overall Accuracy:</b> {metrics['accuracy']:.2%}<br/>"
            f"<b>Precision:</b> {metrics['precision']:.2%}<br/>"
            f"<b>Recall:</b> {metrics['recall']:.2%}<br/>"
            f"<b>F1 Score:</b> {metrics['f1_score']:.2%}"
        )
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(PageBreak())
        
        # Performance Metrics
        story.append(Paragraph("Performance Metrics", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        story.append(self._create_metrics_table(metrics))
        story.append(Spacer(1, 0.3*inch))
        
        # Metrics chart
        metrics_chart = self._generate_metrics_chart(metrics)
        story.append(Image(metrics_chart, width=6*inch, height=4*inch))
        story.append(PageBreak())
        
        # Confusion Matrix
        story.append(Paragraph("Confusion Matrix Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            "The confusion matrix shows the breakdown of true and false predictions "
            "across all evaluated prompts. Green cells indicate correct predictions, "
            "while red cells indicate errors.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(self._create_confusion_matrix_table(metrics))
        story.append(Spacer(1, 0.3*inch))
        
        # Confusion matrix chart
        confusion_chart = self._generate_confusion_matrix_chart(metrics)
        story.append(Image(confusion_chart, width=4.5*inch, height=4*inch))
        story.append(PageBreak())
        
        # Detailed Analysis
        story.append(Paragraph("Detailed Analysis", self.styles['SectionHeader']))
        
        # True Positives
        story.append(Paragraph("True Positives (Correctly Flagged)", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            f"<b>{metrics['true_positive']}</b> malicious prompts were correctly identified. "
            f"This represents <b>{(metrics['true_positive']/metrics['total']*100 if metrics['total'] > 0 else 0):.1f}%</b> of all prompts.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # True Negatives
        story.append(Paragraph("True Negatives (Correctly Cleared)", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            f"<b>{metrics['true_negative']}</b> safe prompts were correctly allowed. "
            f"This represents <b>{(metrics['true_negative']/metrics['total']*100 if metrics['total'] > 0 else 0):.1f}%</b> of all prompts.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # False Positives
        story.append(Paragraph("False Positives (Incorrectly Flagged)", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            f"<b>{metrics['false_positive']}</b> safe prompts were incorrectly flagged as malicious. "
            f"This may lead to user frustration and reduced trust in the system.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # False Negatives
        story.append(Paragraph("False Negatives (Incorrectly Cleared)", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            f"<b>{metrics['false_negative']}</b> malicious prompts were incorrectly allowed. "
            f"This represents a security risk and should be addressed with high priority.",
            self.styles['BodyText']
        ))
        story.append(PageBreak())
        
        # Performance Statistics
        if latency_stats:
            story.append(Paragraph("Performance Statistics", self.styles['SectionHeader']))
            story.append(Spacer(1, 0.2*inch))
            
            # Throughput section
            if 'throughput' in latency_stats:
                story.append(Paragraph("Throughput", self.styles['SubsectionHeader']))
                story.append(Paragraph(
                    f"<b>Overall Throughput:</b> {latency_stats['throughput']:.2f} prompts/sec<br/>"
                    f"<b>Total Prompts Processed:</b> {latency_stats.get('total_prompts', 0)}<br/>"
                    f"<b>Total Elapsed Time:</b> {latency_stats.get('total_time', 0):.2f} seconds",
                    self.styles['BodyText']
                ))
                story.append(Spacer(1, 0.2*inch))
            
            # Latency section with percentiles
            if 'average_latency' in latency_stats:
                story.append(Paragraph("Request Latency", self.styles['SubsectionHeader']))
                
                # Basic stats
                basic_stats = (
                    f"<b>Average:</b> {latency_stats['average_latency']*1000:.2f} ms<br/>"
                    f"<b>Minimum:</b> {latency_stats['min_latency']*1000:.2f} ms<br/>"
                    f"<b>Maximum:</b> {latency_stats['max_latency']*1000:.2f} ms"
                )
                
                # Percentile stats (if available)
                if 'p50_latency' in latency_stats:
                    basic_stats += (
                        f"<br/><br/><b>Latency Percentiles:</b><br/>"
                        f"<b>p50 (median):</b> {latency_stats['p50_latency']*1000:.2f} ms - 50% of requests are faster<br/>"
                        f"<b>p95:</b> {latency_stats['p95_latency']*1000:.2f} ms - 95% of requests are faster<br/>"
                        f"<b>p99:</b> {latency_stats['p99_latency']*1000:.2f} ms - 99% of requests are faster"
                    )
                
                story.append(Paragraph(basic_stats, self.styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
                
                # Add latency chart if percentiles are available
                if 'p50_latency' in latency_stats:
                    latency_chart = self._generate_latency_chart(latency_stats)
                    story.append(Image(latency_chart, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 0.2*inch))
                
                # Interpretation
                story.append(Paragraph(
                    "<b>Understanding Percentiles:</b> Percentiles show the distribution of latency across all requests. "
                    "For example, p95 indicates that 95% of requests completed faster than this time, "
                    "helping identify worst-case user experiences.",
                    self.styles['BodyText']
                ))
            
            story.append(PageBreak())
        
        # Example Errors
        if false_positives or false_negatives:
            story.append(Paragraph("Example Errors", self.styles['SectionHeader']))
            story.append(Spacer(1, 0.2*inch))
            
            if false_positives:
                story.append(Paragraph(
                    f"<b>False Positives Sample</b> (showing first 5 of {len(false_positives)}):",
                    self.styles['SubsectionHeader']
                ))
                story.append(Spacer(1, 0.1*inch))
                
                for i, fp in enumerate(false_positives[:5], 1):
                    prompt_text = self._escape_text(fp.get('prompt', 'N/A'))[:150]
                    if len(fp.get('prompt', '')) > 150:
                        prompt_text += "..."
                    story.append(Paragraph(f"<b>{i}.</b> {prompt_text}", self.styles['BodyText']))
                    story.append(Spacer(1, 0.05*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            if false_negatives:
                story.append(Paragraph(
                    f"<b>False Negatives Sample</b> (showing first 5 of {len(false_negatives)}):",
                    self.styles['SubsectionHeader']
                ))
                story.append(Spacer(1, 0.1*inch))
                
                for i, fn in enumerate(false_negatives[:5], 1):
                    prompt_text = self._escape_text(fn.get('prompt', 'N/A'))[:150]
                    if len(fn.get('prompt', '')) > 150:
                        prompt_text += "..."
                    story.append(Paragraph(f"<b>{i}.</b> {prompt_text}", self.styles['BodyText']))
                    story.append(Spacer(1, 0.05*inch))
            
            story.append(PageBreak())
        
        # Conclusion
        story.append(Paragraph("Conclusion", self.styles['SectionHeader']))
        story.append(Paragraph(
            f"The evaluation of the {self._escape_text(dataset_name)} dataset demonstrates that "
            f"the AI safety scanner achieved an overall accuracy of <b>{metrics['accuracy']:.2%}</b>. "
            f"The scanner correctly identified {metrics['true_positive']} out of "
            f"{metrics['true_positive'] + metrics['false_negative']} malicious prompts "
            f"(recall: {metrics['recall']:.2%}) and correctly allowed "
            f"{metrics['true_negative']} out of {metrics['true_negative'] + metrics['false_positive']} "
            f"safe prompts.",
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            "For optimal performance, consider adjusting the scanner's sensitivity "
            "to balance false positives and false negatives based on your specific use case requirements.",
            self.styles['BodyText']
        ))
        
        # Build PDF
        doc.build(story)
        print(f"✓ PDF report generated: {output_path}")
        return output_path


def load_evaluation_results(dataset_name, results_dir="results", input_file=None):
    """Recompute metrics and examples from one result file, never stale FP/FN sidecars.

    An explicit input filename supports custom evaluator output names. Default
    dataset lookup retains the historical JSONL/CSV/TSV/Parquet precedence.
    """
    result = {"metrics": None, "false_positives": None, "false_negatives": None,
              "latency_stats": None, "evaluation_mode": "legacy"}
    candidates = [input_file] if input_file else [
        os.path.join(results_dir, f"{dataset_name}_results.{extension}")
        for extension in ("jsonl", "csv", "tsv", "parquet")
    ]
    for filename in candidates:
        if not os.path.isfile(filename):
            continue
        records = read_results(filename)
        fps, fns = false_results(records)
        modes = {row.get("evaluation_mode") for row in records if row.get("evaluation_mode")}
        result.update(metrics=calculate_metrics(records), false_positives=fps,
                      false_negatives=fns, latency_stats=latency_statistics(records),
                      evaluation_mode=next(iter(modes)) if len(modes) == 1 else "legacy")
        break
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Generate PDF report from evaluation results'
    )
    parser.add_argument(
        '--dataset', '-d',
        type=str,
        help='Dataset name (e.g., pii_dataset)'
    )
    parser.add_argument(
        '--results-dir', '-r',
        type=str,
        default='results',
        help='Results directory (default: results)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output PDF path (default: results/{dataset}_report.pdf)'
    )
    
    parser.add_argument('--input', '-i', help='Explicit results file, including custom output names')
    args = parser.parse_args()
    if args.input and not args.dataset:
        args.dataset = os.path.splitext(os.path.basename(args.input))[0].removesuffix('_results')
    
    if not args.dataset:
        # Try to find dataset files in results directory
        if os.path.exists(args.results_dir):
            files = os.listdir(args.results_dir)
            datasets = set()
            for f in files:
                # Check for results files in any supported format
                if f.endswith('_results.jsonl'):
                    dataset_name = f.replace('_results.jsonl', '')
                    datasets.add(dataset_name)
                elif f.endswith('_results.csv'):
                    dataset_name = f.replace('_results.csv', '')
                    datasets.add(dataset_name)
                elif f.endswith('_results.tsv'):
                    dataset_name = f.replace('_results.tsv', '')
                    datasets.add(dataset_name)
                elif f.endswith('_results.parquet'):
                    dataset_name = f.replace('_results.parquet', '')
                    datasets.add(dataset_name)
            
            if len(datasets) == 1:
                args.dataset = list(datasets)[0]
                print(f"Auto-detected dataset: {args.dataset}")
            elif len(datasets) > 1:
                print("Multiple datasets found. Please specify one:")
                for ds in sorted(datasets):
                    print(f"  - {ds}")
                return
            else:
                print("No datasets found in results directory.")
                print("Please specify a dataset name with --dataset or run an evaluation first.")
                return
    
    # Load results
    print(f"Loading results for dataset: {args.dataset}")
    results = load_evaluation_results(args.dataset, args.results_dir, args.input)
    
    if not results['metrics']:
        print("Error: Could not load evaluation results.")
        return
    
    # Generate report
    print("Generating PDF report...")
    generator = PDFReportGenerator(args.results_dir)
    output_path = generator.generate_report(
        dataset_name=args.dataset,
        metrics=results['metrics'],
        false_positives=results['false_positives'],
        false_negatives=results['false_negatives'],
        latency_stats=results['latency_stats'],
        output_path=args.output,
        evaluation_mode=results['evaluation_mode']
    )
    
    print(f"\n✓ Report generated successfully!")
    print(f"  File: {output_path}")


if __name__ == "__main__":
    main()
