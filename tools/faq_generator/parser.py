"""State machine parser for FAQ text files.

This module implements a deterministic state machine parser that processes
FAQ entries from a structured text format. The parser is designed to be
resilient to minor formatting variations while maintaining strict validation.

Complexity Analysis:
    - parse_file(): O(n) where n = number of lines in file
    - parse_section(): O(m) where m = lines in section
    - Overall: O(n) single-pass parsing
"""

from __future__ import annotations

import re
from enum import Enum, auto
from pathlib import Path
from typing import Final

from .exceptions import FAQParseError
from .models import RawFAQEntry


class ParserState(Enum):
    """Parser state machine states.
    
    The parser uses a finite state machine to track which section
    is currently being processed. This ensures deterministic parsing
    and clear error reporting.
    """
    
    AWAITING_CATEGORY = auto()
    AWAITING_QUESTION = auto()
    AWAITING_ANSWER = auto()
    IN_ANSWER = auto()
    IN_ALIASES = auto()
    IN_NEXT_STEPS = auto()
    IN_TAGS = auto()


# Regex patterns (compiled once for O(1) reuse)
CATEGORY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\[CATEGORY:\s*([^\]]+)\]$", re.IGNORECASE
)
QUESTION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^Q:\s*(.+)$", re.IGNORECASE)
ANSWER_PATTERN: Final[re.Pattern[str]] = re.compile(r"^A:\s*(.+)$", re.IGNORECASE)
ALIASES_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^ALIASES:\s*(.+)$", re.IGNORECASE
)
NEXT_STEPS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^NEXT_STEPS:\s*$", re.IGNORECASE
)
TAGS_PATTERN: Final[re.Pattern[str]] = re.compile(r"^TAGS:\s*(.+)$", re.IGNORECASE)
BULLET_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[-•]\s*(.+)$")


class FAQParser:
    """State machine parser for FAQ text files.
    
    This parser implements a robust state machine that processes FAQ entries
    line by line. It handles multi-line answers, optional sections, and
    provides detailed error messages with line numbers.
    
    Example:
        >>> parser = FAQParser()
        >>> entries = parser.parse_file(Path("faq.txt"))
        >>> len(entries)
        30
    
    Complexity:
        parse_file: O(n) where n = number of lines
        Memory: O(m) where m = number of FAQ entries
    """
    
    def __init__(self) -> None:
        """Initialize parser with empty state."""
        # Declare instance attributes with types
        self._state: ParserState
        self._category: str
        self._question: str
        self._answer_lines: list[str]
        self._aliases: list[str]
        self._next_steps: list[str]
        self._tags: list[str]
        # Initialize values
        self._reset_state()
    
    def parse_file(self, file_path: Path) -> list[RawFAQEntry]:
        """Parse FAQ text file into structured entries.
        
        Args:
            file_path: Path to the FAQ text file
            
        Returns:
            List of parsed FAQ entries (without IDs assigned)
            
        Raises:
            FAQParseError: If file format is invalid
            FileNotFoundError: If file doesn't exist
            
        Complexity: O(n) where n = number of lines in file
        """
        resolved_path = file_path.resolve()
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"FAQ file not found: {resolved_path}")
        
        if not resolved_path.is_file():
            raise FAQParseError(f"Path is not a file: {resolved_path}", line_no=0)
        
        entries: list[RawFAQEntry] = []
        
        # Stream processing - read line by line to avoid memory issues
        with resolved_path.open("r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                line = line.rstrip("\n\r")
                
                try:
                    # Check if this line starts a new entry
                    if CATEGORY_PATTERN.match(line) and self._is_entry_complete():
                        # Save previous entry before starting new one
                        entries.append(self._build_entry())
                        self._reset_state()
                    
                    self._process_line(line, line_no)
                    
                except Exception as e:
                    raise FAQParseError(
                        f"Parse error: {e}", line_no=line_no
                    ) from e
        
        # Handle final entry
        if self._is_entry_complete():
            entries.append(self._build_entry())
        
        if not entries:
            raise FAQParseError("No FAQ entries found in file", line_no=0)
        
        return entries
    
    def _process_line(self, line: str, line_no: int) -> None:
        """Process a single line based on current state.
        
        This method implements the state machine transitions. It updates
        the internal state and accumulates data based on line content.
        
        Args:
            line: Current line content (stripped)
            line_no: Line number for error reporting
            
        Complexity: O(k) where k = line length
        """
        # Skip empty lines between entries
        if not line.strip():
            return
        
        # Check for section headers (these take precedence over continuation)
        if match := CATEGORY_PATTERN.match(line):
            self._category = match.group(1).strip()
            self._state = ParserState.AWAITING_QUESTION
            return
        
        if match := QUESTION_PATTERN.match(line):
            self._question = match.group(1).strip()
            self._state = ParserState.AWAITING_ANSWER
            return
        
        if match := ANSWER_PATTERN.match(line):
            self._answer_lines.append(match.group(1).strip())
            self._state = ParserState.IN_ANSWER
            return
        
        if match := ALIASES_PATTERN.match(line):
            # Parse comma-separated aliases
            aliases_str = match.group(1).strip()
            self._aliases = [
                alias.strip() 
                for alias in aliases_str.split(",") 
                if alias.strip()
            ]
            # Stay in a state that allows other sections
            return
        
        if NEXT_STEPS_PATTERN.match(line):
            self._state = ParserState.IN_NEXT_STEPS
            return
        
        if match := TAGS_PATTERN.match(line):
            # Parse comma-separated tags
            tags_str = match.group(1).strip()
            self._tags = [
                tag.strip() 
                for tag in tags_str.split(",") 
                if tag.strip()
            ]
            return
        
        # Handle continuation lines based on state
        # (Only reached if line didn't match any section header)
        if self._state == ParserState.IN_ANSWER:
            # Multi-line answer continuation
            self._answer_lines.append(line.strip())
        
        elif self._state == ParserState.IN_NEXT_STEPS:
            # Parse bullet point
            if match := BULLET_PATTERN.match(line):
                step = match.group(1).strip()
                if step:
                    self._next_steps.append(step)
    
    def _is_entry_complete(self) -> bool:
        """Check if current entry has all mandatory fields.
        
        Returns:
            True if entry is complete and valid
            
        Complexity: O(1)
        """
        return bool(
            self._category
            and self._question
            and self._answer_lines
        )
    
    def _build_entry(self) -> RawFAQEntry:
        """Build RawFAQEntry from accumulated state.
        
        Returns:
            Validated RawFAQEntry
            
        Raises:
            ValidationError: If data doesn't meet schema requirements
            
        Complexity: O(k) where k = total content size
        """
        # Join multi-line answer with space
        answer = " ".join(self._answer_lines)
        
        return RawFAQEntry(
            category=self._category,
            q=self._question,
            aliases=self._aliases,
            a=answer,
            next_steps=self._next_steps,
            tags=self._tags,
        )
    
    def _reset_state(self) -> None:
        """Reset parser state for next entry.
        
        Complexity: O(1)
        """
        self._state = ParserState.AWAITING_CATEGORY
        self._category = ""
        self._question = ""
        self._answer_lines = []
        self._aliases = []
        self._next_steps = []
        self._tags = []
