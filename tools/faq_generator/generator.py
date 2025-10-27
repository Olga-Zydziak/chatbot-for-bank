"""Code generator for FAQ entries.

This module generates clean, formatted Python code from FAQ entries.
It uses repr() for safe string escaping and generates idiomatic Python
with proper indentation and formatting.

Complexity Analysis:
    - generate_code(): O(n * m) where n = entries, m = avg fields per entry
    - format_value(): O(k) where k = value size
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .exceptions import FAQGenerationError
from .models import FAQEntry


class FAQCodeGenerator:
    """Generate Python code from FAQ entries.
    
    This generator creates clean, PEP 8-compliant Python code that defines
    FAQ_DATA as a list of dictionaries. It uses repr() for safe string
    escaping and handles nested structures correctly.
    
    Example:
        >>> generator = FAQCodeGenerator()
        >>> code = generator.generate_code(entries)
        >>> print(code[:50])
        # FAQ Data - Auto-generated
        ...
    
    Complexity:
        generate_code: O(n * m) where n = entries, m = fields per entry
        Memory: O(k) where k = total output size
    """
    
    def __init__(self, indent_size: int = 4) -> None:
        """Initialize generator with formatting options.
        
        Args:
            indent_size: Number of spaces per indentation level
        """
        self._indent = " " * indent_size
    
    def generate_code(
        self, 
        entries: list[FAQEntry],
        variable_name: str = "FAQ_DATA",
    ) -> str:
        """Generate Python code defining FAQ data.
        
        Args:
            entries: List of validated FAQ entries
            variable_name: Name of the Python variable to create
            
        Returns:
            Complete Python code as string
            
        Raises:
            FAQGenerationError: If code generation fails
            
        Complexity: O(n * m) where n = entries, m = avg entry size
        """
        if not entries:
            raise FAQGenerationError("Cannot generate code from empty entry list")
        
        lines: list[str] = []
        
        # Header comment
        lines.append("# FAQ Data - Auto-generated")
        lines.append(
            f"# Total entries: {len(entries)}"
        )
        lines.append("")
        
        # Variable declaration
        lines.append(f"{variable_name} = [")
        
        # Generate each entry
        for i, entry in enumerate(entries):
            lines.extend(self._generate_entry(entry, is_last=(i == len(entries) - 1)))
        
        lines.append("]")
        
        return "\n".join(lines)
    
    def write_to_file(
        self,
        entries: list[FAQEntry],
        output_path: Path,
        variable_name: str = "FAQ_DATA",
    ) -> None:
        """Generate code and write to file.
        
        Args:
            entries: List of validated FAQ entries
            output_path: Path to output Python file
            variable_name: Name of the Python variable
            
        Raises:
            FAQGenerationError: If writing fails
            
        Complexity: O(n * m) where n = entries, m = avg entry size
        """
        code = self.generate_code(entries, variable_name)
        
        try:
            resolved_path = output_path.resolve()
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            with resolved_path.open("w", encoding="utf-8") as f:
                f.write(code)
                f.write("\n")  # Final newline
                
        except OSError as e:
            raise FAQGenerationError(
                f"Failed to write to {output_path}: {e}"
            ) from e
    
    def _generate_entry(self, entry: FAQEntry, is_last: bool) -> list[str]:
        """Generate code lines for a single FAQ entry.
        
        Args:
            entry: FAQ entry to generate
            is_last: True if this is the last entry (affects comma)
            
        Returns:
            List of code lines
            
        Complexity: O(m) where m = entry field count
        """
        lines: list[str] = []
        
        # Opening brace with indent
        lines.append(f"{self._indent}{{")
        
        # Generate fields in specific order
        fields = [
            ("id", entry.id),
            ("category", entry.category),
            ("q", entry.q),
            ("aliases", entry.aliases),
            ("a", entry.a),
            ("next_steps", entry.next_steps),
            ("tags", entry.tags),
        ]
        
        for i, (field_name, field_value) in enumerate(fields):
            is_last_field = (i == len(fields) - 1)
            lines.append(
                self._generate_field(field_name, field_value, is_last_field)
            )
        
        # Closing brace
        if is_last:
            lines.append(f"{self._indent}}}")
        else:
            lines.append(f"{self._indent}}},")
        
        return lines
    
    def _generate_field(
        self, 
        name: str, 
        value: Any, 
        is_last: bool
    ) -> str:
        """Generate a single field line.
        
        Args:
            name: Field name
            value: Field value
            is_last: True if this is the last field
            
        Returns:
            Formatted field line
            
        Complexity: O(k) where k = value size
        """
        formatted_value = self._format_value(value, indent_level=2)
        comma = "" if is_last else ","
        return f'{self._indent * 2}"{name}": {formatted_value}{comma}'
    
    def _format_value(self, value: Any, indent_level: int) -> str:
        """Format a Python value for code generation.
        
        Uses repr() for safe escaping of strings and handles
        nested structures (lists) with proper indentation.
        
        Args:
            value: Value to format
            indent_level: Current indentation level
            
        Returns:
            Formatted value string
            
        Complexity: O(k) where k = value size
        """
        if isinstance(value, str):
            # Use repr() for safe escaping
            return repr(value)
        
        elif isinstance(value, list):
            if not value:
                return "[]"
            
            # Multi-line list for readability
            lines = ["["]
            for i, item in enumerate(value):
                item_repr = repr(item)
                comma = "" if i == len(value) - 1 else ","
                lines.append(f"{self._indent * (indent_level + 1)}{item_repr}{comma}")
            lines.append(f"{self._indent * indent_level}]")
            return "\n".join(lines)
        
        else:
            # Numbers, booleans, etc.
            return repr(value)
