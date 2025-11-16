"""Document parsers for AIBooks."""

# Import only what's always available
from .format_detector import FormatDetector, DocumentFormat

# Lazy imports for modules with heavy dependencies
__all__ = [
    "FormatDetector",
    "DocumentFormat",
    "DoclingParser",
    "CalibreMetadataExtractor",
    "MetadataFusion",
]


def __getattr__(name):
    """Lazy import of heavy dependencies."""
    if name == "DoclingParser":
        from .docling_parser import DoclingParser
        return DoclingParser
    elif name == "CalibreMetadataExtractor":
        from .calibre_metadata import CalibreMetadataExtractor
        return CalibreMetadataExtractor
    elif name == "MetadataFusion":
        from .metadata_fusion import MetadataFusion
        return MetadataFusion
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
