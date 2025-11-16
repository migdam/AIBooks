"""Text cleaning and normalization utilities."""

import re
from typing import List, Optional

# Optional imports
try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False

try:
    from unidecode import unidecode
    UNIDECODE_AVAILABLE = True
except ImportError:
    UNIDECODE_AVAILABLE = False


class TextCleaner:
    """Clean and normalize extracted text."""

    def __init__(self):
        """Initialize text cleaner with patterns."""
        # Compile common patterns
        self.hyphenation_pattern = re.compile(r'(\w+)-\s*\n\s*(\w+)')
        self.multiple_spaces_pattern = re.compile(r' {2,}')
        self.multiple_newlines_pattern = re.compile(r'\n{3,}')
        self.page_number_pattern = re.compile(r'^\s*\d+\s*$', re.MULTILINE)
        self.header_footer_pattern = re.compile(
            r'^(?:Chapter \d+|Page \d+|^\d+$)',
            re.MULTILINE | re.IGNORECASE
        )

    def remove_hyphenation(self, text: str) -> str:
        """Remove hyphenation at line breaks.

        Args:
            text: Input text

        Returns:
            Text with hyphenation removed
        """
        return self.hyphenation_pattern.sub(r'\1\2', text)

    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters and fix encoding issues.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Fix mojibake and encoding issues (if ftfy available)
        if FTFY_AVAILABLE:
            text = ftfy.fix_text(text)
        return text

    def normalize_quotes(self, text: str) -> str:
        """Normalize various quote types.

        Args:
            text: Input text

        Returns:
            Text with normalized quotes
        """
        # Smart quotes to straight quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('„', '"').replace('‟', '"')
        return text

    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace.

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = self.multiple_spaces_pattern.sub(' ', text)

        # Replace multiple newlines with max 2
        text = self.multiple_newlines_pattern.sub('\n\n', text)

        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))

        return text.strip()

    def remove_page_numbers(self, text: str) -> str:
        """Remove standalone page numbers.

        Args:
            text: Input text

        Returns:
            Text with page numbers removed
        """
        return self.page_number_pattern.sub('', text)

    def remove_ocr_artifacts(self, text: str) -> str:
        """Remove common OCR artifacts.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Remove common OCR errors
        replacements = {
            '|': 'I',  # Common OCR mistake
            '0': 'O',  # In certain contexts
            '¥': 'Y',
            '§': 'S',
        }

        # Only apply in specific contexts (e.g., when surrounded by letters)
        for old, new in replacements.items():
            # Pattern: letter + artifact + letter
            pattern = re.compile(f'([a-zA-Z]){re.escape(old)}([a-zA-Z])')
            text = pattern.sub(f'\\1{new}\\2', text)

        # Remove excessive dots (OCR noise)
        text = re.sub(r'\.{4,}', '...', text)

        # Remove lone special characters
        text = re.sub(r'\s[~`!@#$%^&*()_+=\[\]{}|\\:;"\'<>,.?/]\s', ' ', text)

        return text

    def remove_headers_footers(self, text: str, patterns: Optional[List[str]] = None) -> str:
        """Remove headers and footers.

        Args:
            text: Input text
            patterns: Additional regex patterns to match

        Returns:
            Text with headers/footers removed
        """
        # Default pattern
        text = self.header_footer_pattern.sub('', text)

        # Custom patterns
        if patterns:
            for pattern in patterns:
                text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)

        return text

    def clean(
        self,
        text: str,
        remove_hyphenation: bool = True,
        normalize_unicode: bool = True,
        normalize_quotes: bool = True,
        normalize_whitespace: bool = True,
        remove_page_numbers: bool = True,
        remove_ocr_artifacts: bool = True,
        remove_headers_footers: bool = False,
    ) -> str:
        """Comprehensive text cleaning.

        Args:
            text: Input text
            remove_hyphenation: Remove line-break hyphenation
            normalize_unicode: Fix Unicode/encoding issues
            normalize_quotes: Normalize quote characters
            normalize_whitespace: Normalize spaces and newlines
            remove_page_numbers: Remove standalone page numbers
            remove_ocr_artifacts: Remove OCR artifacts
            remove_headers_footers: Remove common headers/footers

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        if remove_hyphenation:
            text = self.remove_hyphenation(text)

        if normalize_unicode:
            text = self.normalize_unicode(text)

        if normalize_quotes:
            text = self.normalize_quotes(text)

        if remove_page_numbers:
            text = self.remove_page_numbers(text)

        if remove_ocr_artifacts:
            text = self.remove_ocr_artifacts(text)

        if remove_headers_footers:
            text = self.remove_headers_footers(text)

        if normalize_whitespace:
            text = self.normalize_whitespace(text)

        return text


# Convenience function
def clean_text(text: str, **kwargs) -> str:
    """Clean text using default settings.

    Args:
        text: Input text
        **kwargs: Additional arguments for TextCleaner.clean()

    Returns:
        Cleaned text
    """
    cleaner = TextCleaner()
    return cleaner.clean(text, **kwargs)
