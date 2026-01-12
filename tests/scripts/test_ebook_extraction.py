"""
Validate ebook extraction output against a reference text.

Usage:
  python tests/scripts/test_ebook_extraction.py \
    --ebook tests/samples/ebooks/test.epub \
    --reference tests/ground_truth/ebooks/midsummer_reference.txt
"""

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path
from typing import List, Tuple


def _load_ebook_parser(repo_root: Path):
    parser_path = repo_root / "infra" / "docker" / "ebook-parser" / "ebook_parser.py"
    spec = importlib.util.spec_from_file_location("ebook_parser", parser_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load ebook_parser module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def levenshtein(seq_a: List[str], seq_b: List[str]) -> int:
    if seq_a == seq_b:
        return 0
    if not seq_a:
        return len(seq_b)
    if not seq_b:
        return len(seq_a)

    prev_row = list(range(len(seq_b) + 1))
    for i, token_a in enumerate(seq_a, start=1):
        current = [i]
        for j, token_b in enumerate(seq_b, start=1):
            insertions = prev_row[j] + 1
            deletions = current[j - 1] + 1
            substitutions = prev_row[j - 1] + (token_a != token_b)
            current.append(min(insertions, deletions, substitutions))
        prev_row = current
    return prev_row[-1]


def compute_wer(reference: str, hypothesis: str) -> float:
    ref_tokens = normalize(reference).split()
    hyp_tokens = normalize(hypothesis).split()
    if not ref_tokens:
        return 0.0
    return levenshtein(ref_tokens, hyp_tokens) / len(ref_tokens)


def compute_cer(reference: str, hypothesis: str) -> float:
    ref_chars = list(normalize(reference))
    hyp_chars = list(normalize(hypothesis))
    if not ref_chars:
        return 0.0
    return levenshtein(ref_chars, hyp_chars) / len(ref_chars)


def compute_completeness(reference: str, hypothesis: str) -> float:
    ref_len = len(normalize(reference))
    hyp_len = len(normalize(hypothesis))
    if ref_len == 0:
        return 0.0
    return min(hyp_len / ref_len, 1.0)


def evaluate(ebook_path: Path, reference_path: Path) -> Tuple[float, float, float]:
    repo_root = Path(__file__).resolve().parents[2]
    parser_module = _load_ebook_parser(repo_root)

    result = parser_module.parse_ebook(ebook_path)
    hypothesis = result.get("text", "")
    reference = reference_path.read_text(encoding="utf-8")

    return (
        compute_wer(reference, hypothesis),
        compute_cer(reference, hypothesis),
        compute_completeness(reference, hypothesis),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ebook extraction output.")
    parser.add_argument("--ebook", type=Path, required=True, help="Path to ebook file")
    parser.add_argument("--reference", type=Path, required=True, help="Path to reference text")
    args = parser.parse_args()

    if not args.ebook.exists():
        raise FileNotFoundError(f"Ebook not found: {args.ebook}")
    if not args.reference.exists():
        raise FileNotFoundError(f"Reference text not found: {args.reference}")

    wer, cer, completeness = evaluate(args.ebook, args.reference)

    print("Ebook extraction evaluation")
    print(f"- WER: {wer:.4f}")
    print(f"- CER: {cer:.4f}")
    print(f"- Completeness: {completeness:.4f}")


if __name__ == "__main__":
    main()
