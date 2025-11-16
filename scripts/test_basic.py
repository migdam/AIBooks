#!/usr/bin/env python3
"""Basic functionality test without requiring all dependencies."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test basic imports."""
    print("Testing imports...")

    try:
        from aibooks.parsers.format_detector import FormatDetector, DocumentFormat
        print("✅ format_detector imports OK")
    except Exception as e:
        print(f"❌ format_detector import failed: {e}")
        return False

    try:
        from aibooks.utils.hash_utils import calculate_content_hash
        print("✅ hash_utils imports OK")
    except Exception as e:
        print(f"❌ hash_utils import failed: {e}")
        return False

    try:
        from aibooks.utils.text_cleaner import TextCleaner
        print("✅ text_cleaner imports OK")
    except Exception as e:
        print(f"❌ text_cleaner import failed: {e}")
        return False

    return True


def test_format_detection():
    """Test format detection."""
    print("\nTesting format detection...")

    from aibooks.parsers.format_detector import FormatDetector, DocumentFormat

    detector = FormatDetector()

    # Test extension detection
    tests = [
        (Path("test.pdf"), DocumentFormat.PDF),
        (Path("test.epub"), DocumentFormat.EPUB),
        (Path("test.docx"), DocumentFormat.DOCX),
        (Path("test.txt"), DocumentFormat.TXT),
    ]

    for path, expected in tests:
        result = detector.detect_from_extension(path)
        if result == expected:
            print(f"✅ {path.suffix} -> {result}")
        else:
            print(f"❌ {path.suffix}: expected {expected}, got {result}")
            return False

    return True


def test_text_cleaning():
    """Test text cleaning."""
    print("\nTesting text cleaning...")

    from aibooks.utils.text_cleaner import TextCleaner

    cleaner = TextCleaner()

    # Test hyphenation removal
    text = "This is a sen-\ntence"
    cleaned = cleaner.remove_hyphenation(text)
    if "sentence" in cleaned and "sen-\n" not in cleaned:
        print("✅ Hyphenation removal works")
    else:
        print("❌ Hyphenation removal failed")
        return False

    # Test whitespace normalization
    text = "Too    many     spaces"
    cleaned = cleaner.normalize_whitespace(text)
    if "    " not in cleaned:
        print("✅ Whitespace normalization works")
    else:
        print("❌ Whitespace normalization failed")
        return False

    return True


def test_hashing():
    """Test content hashing."""
    print("\nTesting content hashing...")

    from aibooks.utils.hash_utils import calculate_content_hash

    # Same content should produce same hash
    hash1 = calculate_content_hash("test content")
    hash2 = calculate_content_hash("test content")

    if hash1 == hash2:
        print("✅ Hash consistency OK")
    else:
        print("❌ Hash consistency failed")
        return False

    # Different content should produce different hashes
    hash3 = calculate_content_hash("different content")

    if hash1 != hash3:
        print("✅ Hash uniqueness OK")
    else:
        print("❌ Hash uniqueness failed")
        return False

    # Check hash length (SHA-256)
    if len(hash1) == 64:
        print("✅ Hash length OK (SHA-256)")
    else:
        print(f"❌ Hash length wrong: {len(hash1)} (expected 64)")
        return False

    return True


def main():
    """Run all tests."""
    print("="* 60)
    print("AIBooks Basic Functionality Tests")
    print("=" * 60)
    print()

    tests = [
        ("Imports", test_imports),
        ("Format Detection", test_format_detection),
        ("Text Cleaning", test_text_cleaning),
        ("Content Hashing", test_hashing),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
