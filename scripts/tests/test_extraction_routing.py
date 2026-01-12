"""
Test: Docling-First Extraction Routing
=======================================

Testet die Unified Extraction Service Integration.
"""

import sys
import io
from pathlib import Path

# Fix Windows Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Projekt-Root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.parser_routing import (
    get_parser, get_fallback_chain, get_parser_config,
    ParserType, get_routing_stats
)
from config.feature_flags import is_enabled


def test_parser_routing():
    """Testet das Parser Routing."""
    print("=" * 60)
    print("TEST: Parser Routing")
    print("=" * 60)

    # Test verschiedene Extensions
    test_cases = [
        (".pdf", ParserType.DOCLING),
        (".docx", ParserType.DOCLING),
        (".xlsx", ParserType.DOCLING),
        (".doc", ParserType.TIKA),
        (".jpg", ParserType.SURYA),
        (".mp3", ParserType.WHISPERX),
        (".zip", ParserType.ARCHIVE),
        (".unknown", ParserType.TIKA),  # Default
    ]

    passed = 0
    failed = 0

    for ext, expected in test_cases:
        result = get_parser(ext)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"  {status} {ext} → {result.value} (expected: {expected.value})")

    print(f"\nResult: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_fallback_chains():
    """Testet Fallback Chains."""
    print("\n" + "=" * 60)
    print("TEST: Fallback Chains")
    print("=" * 60)

    test_cases = [
        (".pdf", [ParserType.DOCLING, ParserType.TIKA]),
        (".jpg", [ParserType.SURYA, ParserType.TIKA]),
        (".mp3", [ParserType.WHISPERX]),
        (".doc", [ParserType.TIKA]),
    ]

    passed = 0
    for ext, expected in test_cases:
        result = get_fallback_chain(ext)
        status = "✅" if result == expected else "❌"

        if result == expected:
            passed += 1

        print(f"  {status} {ext} → {[p.value for p in result]}")

    print(f"\nResult: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_feature_flags():
    """Testet Feature Flags."""
    print("\n" + "=" * 60)
    print("TEST: Feature Flags")
    print("=" * 60)

    flags = [
        "USE_PARSER_ROUTING",
        "USE_DOCLING_FIRST",
        "USE_SURYA_OCR",
        "USE_WHISPERX",
    ]

    for flag in flags:
        enabled = is_enabled(flag)
        status = "✅ ON" if enabled else "⬜ OFF"
        print(f"  {status} {flag}")

    # USE_PARSER_ROUTING muss aktiviert sein
    return is_enabled("USE_PARSER_ROUTING")


def test_routing_stats():
    """Zeigt Routing-Statistiken."""
    print("\n" + "=" * 60)
    print("TEST: Routing Stats")
    print("=" * 60)

    stats = get_routing_stats()

    print(f"\n  Total Extensions: {stats['total_extensions']}")
    print("\n  By Parser:")
    for parser, count in stats['by_parser'].items():
        print(f"    {parser}: {count}")

    print(f"\n  Docling-First: {stats['docling_first_extensions']}")
    return True


def test_extraction_service():
    """Testet den Extraction Service."""
    print("\n" + "=" * 60)
    print("TEST: Extraction Service Status")
    print("=" * 60)

    try:
        from scripts.services.extraction_service import get_extraction_stats

        stats = get_extraction_stats()

        print("\n  Service Availability:")
        for service, available in stats["services"].items():
            icon = "✅" if available else "❌"
            print(f"    {icon} {service}")

        print("\n  Feature Flags:")
        for flag, enabled in stats["feature_flags"].items():
            icon = "✅" if enabled else "⬜"
            print(f"    {icon} {flag}")

        return True

    except ImportError as e:
        print(f"  ❌ Import Error: {e}")
        return False


def main():
    """Führt alle Tests aus."""
    print("\n" + "=" * 60)
    print("DOCLING-FIRST EXTRACTION ROUTING TESTS")
    print("=" * 60 + "\n")

    results = []

    results.append(("Parser Routing", test_parser_routing()))
    results.append(("Fallback Chains", test_fallback_chains()))
    results.append(("Feature Flags", test_feature_flags()))
    results.append(("Routing Stats", test_routing_stats()))
    results.append(("Extraction Service", test_extraction_service()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"  {icon} {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print("\n  ⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
