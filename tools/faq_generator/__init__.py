"""FAQ Generator - Convert text FAQ files to Python code.

This package provides a robust, type-safe solution for converting structured
FAQ text files into Python code with full validation and error handling.

Public API:
    - FAQConverter: Main conversion service
    - FAQParser: Text file parser
    - FAQCodeGenerator: Python code generator
    - FAQEntry: Validated FAQ entry model
    - All custom exceptions

Example:
    >>> from faq_generator import FAQConverter
    >>> converter = FAQConverter()
    >>> code = converter.convert_file(Path("faq.txt"), Path("output.py"))

Author: Principal Systems Architect (L10)
Python: 3.10+
License: MIT
"""

from __future__ import annotations

from .converter import FAQConverter
from .exceptions import (
    FAQGenerationError,
    FAQGeneratorError,
    FAQParseError,
    FAQValidationError,
)
from .generator import FAQCodeGenerator
from .models import FAQEntry, RawFAQEntry
from .parser import FAQParser

__version__ = "1.0.0"

__all__ = [
    # Main API
    "FAQConverter",
    "FAQParser",
    "FAQCodeGenerator",
    # Models
    "FAQEntry",
    "RawFAQEntry",
    # Exceptions
    "FAQGeneratorError",
    "FAQParseError",
    "FAQValidationError",
    "FAQGenerationError",
    # Metadata
    "__version__",
]