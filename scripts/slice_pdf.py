#!/usr/bin/env python3
"""Slice an Indian listed company PDF into per-section extracts.

Usage:
    python scripts/slice_pdf.py <pdf_path> [--type ar|concall|auto] [--out DIR]

Auto-detects type from filename when --type is omitted:
- "AR-..." or filename containing "annual" / "ar-fy" / "drhp"  -> ar
- "concall-..." or filename containing "concall" / "transcript" -> concall

Writes extracts to <pdf_dir>/../extracts/ by default. Prints a JSON summary
to stdout listing every file written, line counts, and any section the grep
heuristics could not locate (so the running model can patch boundaries by
hand).

This script does *not* invent topic tags for concall Q&A turns — it leaves
the index.json topics arrays empty. The running Claude session fills them
inline by reading each turn (see references/pdf-slicing.md).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

AR_SECTIONS = [
    ("mdna", r"management(?:'s)?\s+discussion\s+(?:and|&)\s+analysis"),
    ("directors-report", r"director.?s?\s+report\b|board.?s?\s+report\b"),
    ("auditor-report", r"independent\s+auditor.?s?\s+report"),
    ("caro", r"\bCARO\s*(?:2020|2016)?\b|annexure\s+(?:[ab]|to|of)\s+(?:the\s+)?independent\s+auditor"),
    ("segments", r"(?:operating\s+segments?|segment\s+(?:reporting|information))"),
    ("rpt", r"related\s+party\s+(?:transactions?|disclosures?)"),
    ("contingent-liab", r"contingent\s+liabilit(?:y|ies)\s+and\s+commitments?|contingent\s+liabilit(?:y|ies)"),
    ("borrowings", r"\bborrowings\b"),
    ("aoc1", r"form\s+aoc[\s\-]?1|salient\s+features.*subsidiar"),
    ("esop", r"employee\s+stock\s+option(?:\s+(?:plan|scheme))?|managerial\s+remuneration"),
]

QA_BOUNDARY_PATTERNS = [
    r"^\s*moderator\b",
    r"question\s*(and|&)\s*answer",
    r"q\s*&\s*a\s*session",
    r"first\s+question",
    r"interactive\s+session",
]

TURN_PATTERNS = [
    r"^\s*(moderator|operator)\s*[:.]",
    r"next\s+question.{0,10}from",
    r"question\s+from\s+the\s+line\s+of",
]

ANALYST_LINE = re.compile(
    r"(?:[Ll]ine\s+of|[Qq]uestion\s+(?:is\s+)?from|[Cc]omes\s+from)\s+"
    r"(?:Mr\.?|Ms\.?|Mrs\.?)?\s*"
    r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})"
    r"\s+from\s+"
    r"(?P<firm>[A-Z][A-Za-z0-9&.\s\-]{2,60}?)"
    r"(?:\s*[\.,;]|\s+please|\s+go\s+ahead|\s*$|\n)",
)


@dataclass
class Match:
    section: str
    line: int


def detect_type(name: str) -> str:
    n = name.lower()
    if "concall" in n or "transcript" in n:
        return "concall"
    if "ar-" in n or "annual" in n or "drhp" in n or "rhp-" in n:
        return "ar"
    return "ar"


def run_pdftotext(pdf: Path, out: Path) -> None:
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext not found. Install poppler: brew install poppler")
    subprocess.run(
        ["pdftotext", "-layout", str(pdf), str(out)],
        check=True,
    )
    if out.stat().st_size < 500:
        sys.exit(
            f"pdftotext produced near-empty output ({out.stat().st_size} bytes). "
            f"PDF may be image-based — rerun: ocrmypdf {pdf} {pdf.with_suffix('.ocr.pdf')}"
        )


def looks_like_heading(line: str, prev: str, next_line: str) -> bool:
    """A line is heading-shaped if it's short, set off, and not a sentence.

    Real section headings in ARs/RHPs are typically:
    - <= 100 chars
    - mostly uppercase OR title case
    - preceded by a blank line (or form-feed)
    - not ending with a period (sentence)
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False
    if stripped.endswith(".") and not stripped.endswith("..."):
        return False
    if not (prev.strip() == "" or "\f" in prev):
        return False
    letters = [c for c in stripped if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio >= 0.6:
        return True
    words = stripped.split()
    if not words:
        return False
    title_words = sum(1 for w in words if w[:1].isupper())
    return title_words / len(words) >= 0.6


def find_section_starts(text: str) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    """Return (heading_matches, all_matches) per section.

    heading_matches: lines that match the pattern AND look like a heading.
    all_matches: every line where the pattern appears (for the model to inspect
    when heading detection misses a real section).
    """
    lines = text.splitlines()
    heading: dict[str, list[int]] = {name: [] for name, _ in AR_SECTIONS}
    everywhere: dict[str, list[int]] = {name: [] for name, _ in AR_SECTIONS}
    compiled = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in AR_SECTIONS]
    for i, line in enumerate(lines, 1):
        for name, rx in compiled:
            if not rx.search(line):
                continue
            everywhere[name].append(i)
            prev = lines[i - 2] if i >= 2 else ""
            nxt = lines[i] if i < len(lines) else ""
            if looks_like_heading(line, prev, nxt):
                heading[name].append(i)
    return heading, everywhere


def pick_real_starts(heading: dict[str, list[int]], everywhere: dict[str, list[int]]) -> dict[str, int]:
    """For each section, prefer the LAST heading-shaped match (real section
    bodies usually appear after TOC repetitions). Fall back to the last
    everywhere-match only if heading detection found nothing.
    """
    real: dict[str, int] = {}
    for name in heading:
        if heading[name]:
            real[name] = heading[name][-1]
        elif everywhere[name]:
            real[name] = everywhere[name][-1]
    return real


def slice_ar(pdf: Path, out_dir: Path, dry_run: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf.stem
    full_text_path = out_dir / f"{stem}.txt"
    run_pdftotext(pdf, full_text_path)

    text = full_text_path.read_text(errors="replace")
    lines = text.splitlines()
    total = len(lines)

    heading_hits, all_hits = find_section_starts(text)
    starts = pick_real_starts(heading_hits, all_hits)
    ordered = sorted(starts.items(), key=lambda kv: kv[1])

    written: list[dict] = []
    suspicious: list[str] = []
    missing = [name for name, _ in AR_SECTIONS if name not in starts]

    for idx, (name, start) in enumerate(ordered):
        end = ordered[idx + 1][1] - 1 if idx + 1 < len(ordered) else total
        section_lines = end - start + 1
        suspicious_section = section_lines > 3000 or section_lines < 5
        if suspicious_section:
            suspicious.append(name)
        entry = {
            "section": name,
            "start_line": start,
            "end_line": end,
            "lines": section_lines,
            "heading_match": name in heading_hits and start in heading_hits[name],
            "header_text": lines[start - 1].strip()[:120],
        }
        if not dry_run:
            section_text = "\n".join(lines[start - 1:end])
            out_path = out_dir / f"{stem}-{name}.txt"
            out_path.write_text(section_text)
            entry["file"] = str(out_path)
        written.append(entry)

    return {
        "type": "ar",
        "source": str(pdf),
        "full_text": str(full_text_path),
        "total_lines": total,
        "dry_run": dry_run,
        "sections_written": written,
        "sections_missing": missing,
        "sections_suspicious": suspicious,
        "heading_hits": heading_hits,
        "all_hits": all_hits,
    }


def find_qa_boundary(lines: list[str]) -> int | None:
    rx = [re.compile(p, re.IGNORECASE) for p in QA_BOUNDARY_PATTERNS]
    for i, line in enumerate(lines, 1):
        if any(r.search(line) for r in rx):
            return i
    return None


def find_turn_starts(lines: list[str], qa_start: int) -> list[int]:
    rx = [re.compile(p, re.IGNORECASE) for p in TURN_PATTERNS]
    turns: list[int] = []
    for i in range(qa_start, len(lines) + 1):
        line = lines[i - 1]
        if any(r.search(line) for r in rx):
            turns.append(i)
    return turns


def parse_analyst(snippet: str) -> tuple[str, str]:
    flat = re.sub(r"\s+", " ", snippet)
    m = ANALYST_LINE.search(flat)
    if not m:
        return ("unknown-analyst", "unknown-firm")
    name = re.sub(r"\s+", "-", m.group("name").strip())
    firm_raw = m.group("firm").strip()
    firm_raw = re.split(r"\s+(?:please|go\s+ahead|your\s+line)", firm_raw, maxsplit=1)[0]
    firm = re.sub(r"[^A-Za-z0-9]+", "", firm_raw) or "unknown-firm"
    return (name, firm)


def slice_concall(pdf: Path, out_dir: Path, dry_run: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf.stem
    full_text_path = out_dir / f"{stem}.txt"
    run_pdftotext(pdf, full_text_path)

    text = full_text_path.read_text(errors="replace")
    lines = text.splitlines()
    total = len(lines)

    qa_start = find_qa_boundary(lines)
    if qa_start is None:
        return {
            "type": "concall",
            "source": str(pdf),
            "full_text": str(full_text_path),
            "total_lines": total,
            "error": "Q&A boundary not found — falling back to whole-file feed",
        }

    opening_path = out_dir / f"{stem}-opening-remarks.txt"
    if not dry_run:
        opening_path.write_text("\n".join(lines[:qa_start - 1]))

    turn_starts = find_turn_starts(lines, qa_start)
    qa_dir = out_dir / f"{stem}-qa"
    if not dry_run:
        qa_dir.mkdir(exist_ok=True)

    turns: list[dict] = []
    for i, start in enumerate(turn_starts, 1):
        end = turn_starts[i] - 1 if i < len(turn_starts) else total
        turn_text = "\n".join(lines[start - 1:end])
        snippet = "\n".join(lines[start - 1:start + 5])
        analyst, firm = parse_analyst(snippet)
        fname = f"q{i:02d}-{analyst}-{firm}.txt"
        out_file = qa_dir / fname
        if not dry_run:
            out_file.write_text(turn_text)
        turns.append({
            "q": i,
            "analyst": analyst.replace("-", " "),
            "firm": firm,
            "topics": [],
            "file": str(out_file),
            "start_line": start,
            "end_line": end,
        })

    index_path = out_dir / f"{stem}-index.json"
    if not dry_run:
        index_path.write_text(json.dumps(turns, indent=2))

    return {
        "type": "concall",
        "source": str(pdf),
        "full_text": str(full_text_path),
        "total_lines": total,
        "qa_boundary_line": qa_start,
        "opening_remarks": str(opening_path),
        "qa_dir": str(qa_dir),
        "index": str(index_path),
        "turns_written": len(turns),
        "note": "topics arrays are empty — the running model fills them by reading each turn",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pdf", type=Path)
    p.add_argument("--type", choices=("ar", "concall", "auto"), default="auto")
    p.add_argument("--out", type=Path, help="Output dir (default: <pdf_dir>/../extracts)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be sliced without writing files. Use to verify boundaries.")
    args = p.parse_args()

    if not args.pdf.exists():
        sys.exit(f"PDF not found: {args.pdf}")

    doctype = args.type if args.type != "auto" else detect_type(args.pdf.name)
    out_dir = args.out or args.pdf.parent.parent / "extracts"

    if doctype == "ar":
        result = slice_ar(args.pdf, out_dir, dry_run=args.dry_run)
    else:
        result = slice_concall(args.pdf, out_dir, dry_run=args.dry_run)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
