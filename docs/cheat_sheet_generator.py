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

#!/usr/bin/env python3
"""Build the public PDF quick reference from CHEAT_SHEET.md.

Run from any working directory in the project Conda environment. Only local
Markdown is read; no credentials, result artifacts, or network calls are needed.
"""

import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, XPreformatted


def _inline(text):
    """Render the supported inline Markdown safely, using link labels for print."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', escape(text))


def _code(text):
    """Wrap long shell commands with executable continuations, not truncated text."""
    lines = []
    wrapper = textwrap.TextWrapper(
        width=94, subsequent_indent="  ", break_long_words=False, break_on_hyphens=False
    )
    for line in text.splitlines():
        if len(line) > 94 and line.startswith(("python ", "conda ", "git ")):
            parts = wrapper.wrap(line)
            lines.extend(part + " \\" for part in parts[:-1])
            lines.append(parts[-1])
        else:
            lines.append(line)
    return escape("\n".join(lines))


def _styles():
    """Return styles for the limited headings, paragraphs, lists, and fenced code."""
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "QuickTitle",
            parent=styles["Title"],
            fontSize=21,
            leading=25,
            textColor=colors.HexColor("#243746"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            "QuickHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#225b88"),
            spaceBefore=13,
            spaceAfter=8,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            "QuickBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            "QuickCode",
            fontName="Courier",
            fontSize=8,
            leading=11,
            backColor=colors.HexColor("#f1f4f7"),
            borderPadding=6,
            spaceAfter=12,
        )
    )
    return styles


def _story(markdown, styles):
    """Convert supported Markdown to flowables; reject an unclosed code fence."""
    story = []
    paragraph = []
    code = []
    in_code = False

    def flush_paragraph():
        """Emit accumulated prose before a heading, code block, or blank line."""
        if paragraph:
            story.append(Paragraph(_inline(" ".join(paragraph)), styles["QuickBody"]))
            paragraph.clear()

    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(XPreformatted(_code("\n".join(code)), styles["QuickCode"]))
                story.append(Spacer(1, 4))
                code.clear()
            in_code = not in_code
        elif in_code:
            code.append(raw)
        elif not line:
            flush_paragraph()
        elif line.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(_inline(line[2:]), styles["QuickTitle"]))
        elif line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(_inline(line[3:]), styles["QuickHeading"]))
        elif line.startswith(("- ", "* ")):
            flush_paragraph()
            story.append(
                Paragraph(_inline(line[2:]), styles["QuickBody"], bulletText="•")
            )
        else:
            paragraph.append(line)
    if in_code:
        raise ValueError("Quick-reference Markdown contains an unclosed code fence")
    flush_paragraph()
    return story


def generate_cheat_sheet(output_path=None):
    """Write a PDF from the adjacent quick-reference Markdown and return its path.

    The default destination is the published documentation PDF. An alternate PDF
    path can be supplied for verification without replacing the published asset.
    """
    source = Path(__file__).with_name("CHEAT_SHEET.md")
    target = (
        Path(output_path)
        if output_path
        else source.with_name("prompt_evaluator_cheat_sheet.pdf")
    )
    if target.suffix.lower() != ".pdf":
        raise ValueError("Quick-reference output must be a PDF file")
    flowables = _story(source.read_text(encoding="utf-8"), _styles())
    target.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(target),
        pagesize=letter,
        leftMargin=42,
        rightMargin=42,
        topMargin=38,
        bottomMargin=38,
        title="Prompt evaluator quick reference",
        author="prompt-evaluator",
    ).build(flowables)
    print(f"Quick-reference PDF generated: {target}")
    return str(target)


if __name__ == "__main__":
    generate_cheat_sheet()
