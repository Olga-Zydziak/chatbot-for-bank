"""Custom exceptions for FAQ generator.

This module defines a hierarchical exception structure for clear error handling
and reporting. All exceptions include context information for debugging.

Complexity: O(1) for all exception operations
"""

from __future__ import annotations


class FAQGeneratorError(Exception):
    """Base exception for all FAQ generator errors.
    
    This is the root of the exception hierarchy. Catching this exception
    will catch all FAQ generator-specific errors.
    """
    
    pass


class FAQParseError(FAQGeneratorError):
    """Raised when FAQ text file parsing fails.
    
    This exception includes the line number where the error occurred
    for precise error reporting.
    
    Attributes:
        message: Human-readable error description
        line_no: Line number where error occurred (0 if not line-specific)
    """
    
    def __init__(self, message: str, line_no: int = 0) -> None:
        """Initialize parse error with context.
        
        Args:
            message: Error description
            line_no: Line number (0 for file-level errors)
        """
        self.line_no = line_no
        if line_no > 0:
            super().__init__(f"Line {line_no}: {message}")
        else:
            super().__init__(message)


class FAQValidationError(FAQGeneratorError):
    """Raised when FAQ entry validation fails.
    
    This wraps Pydantic ValidationErrors with additional context
    about which entry failed validation.
    
    Attributes:
        message: Human-readable error description
        entry_index: Index of the entry that failed (if applicable)
    """
    
    def __init__(self, message: str, entry_index: int | None = None) -> None:
        """Initialize validation error with context.
        
        Args:
            message: Error description
            entry_index: Optional index of failed entry
        """
        self.entry_index = entry_index
        if entry_index is not None:
            super().__init__(f"Entry {entry_index + 1}: {message}")
        else:
            super().__init__(message)


class FAQGenerationError(FAQGeneratorError):
    """Raised when code generation fails.
    
    This exception indicates a failure in the code generation phase,
    such as file I/O errors or formatting issues.
    """
    
    pass
