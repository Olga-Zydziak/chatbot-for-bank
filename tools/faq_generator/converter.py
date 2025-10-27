"""Main FAQ converter service.

This module provides the high-level orchestration for converting FAQ text
files to Python code. It coordinates the parser, validator, and generator
components.

Complexity: O(n) where n = total content size
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import FAQValidationError
from .generator import FAQCodeGenerator
from .models import FAQEntry, RawFAQEntry
from .parser import FAQParser


class FAQConverter:
    """High-level FAQ conversion service.
    
    This class orchestrates the complete conversion pipeline:
    1. Parse text file → RawFAQEntry list
    2. Assign IDs → FAQEntry list  
    3. Generate Python code
    4. Write to output file (optional)
    
    Example:
        >>> converter = FAQConverter()
        >>> code = converter.convert_file(Path("faq.txt"))
        >>> print(code[:100])
        # FAQ Data - Auto-generated...
    
    Complexity:
        convert_file: O(n) where n = total file size
        Memory: O(m) where m = number of entries
    """
    
    def __init__(
        self,
        parser: FAQParser | None = None,
        generator: FAQCodeGenerator | None = None,
    ) -> None:
        """Initialize converter with optional custom components.
        
        Args:
            parser: Custom parser instance (uses default if None)
            generator: Custom generator instance (uses default if None)
        """
        self._parser = parser or FAQParser()
        self._generator = generator or FAQCodeGenerator()
    
    def convert_file(
        self,
        input_path: Path,
        output_path: Path | None = None,
        variable_name: str = "FAQ_DATA",
    ) -> str:
        """Convert FAQ text file to Python code.
        
        This is the main entry point for the conversion process. It reads
        the text file, parses it, validates all entries, generates Python
        code, and optionally writes to an output file.
        
        Args:
            input_path: Path to FAQ text file
            output_path: Optional path to output Python file
            variable_name: Name of Python variable to generate
            
        Returns:
            Generated Python code as string
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            FAQParseError: If file format is invalid
            FAQValidationError: If entry validation fails
            FAQGenerationError: If code generation fails
            
        Complexity: O(n) where n = total file size
        """
        # Phase 1: Parse text file
        raw_entries = self._parser.parse_file(input_path)
        
        # Phase 2: Assign IDs and validate
        entries = self._assign_ids_and_validate(raw_entries)
        
        # Phase 3: Generate code
        code = self._generator.generate_code(entries, variable_name)
        
        # Phase 4: Write to file if requested
        if output_path is not None:
            self._generator.write_to_file(entries, output_path, variable_name)
        
        return code
    
    def convert_multiple_files(
        self,
        input_paths: list[Path],
        output_path: Path,
        variable_name: str = "FAQ_DATA",
    ) -> str:
        """Convert multiple FAQ files into a single output.
        
        This method allows combining FAQ entries from multiple source files
        into a single Python variable. IDs are assigned sequentially across
        all files.
        
        Args:
            input_paths: List of FAQ text file paths
            output_path: Path to output Python file
            variable_name: Name of Python variable to generate
            
        Returns:
            Generated Python code as string
            
        Raises:
            Same exceptions as convert_file()
            
        Complexity: O(n * m) where n = files, m = avg file size
        """
        all_entries: list[FAQEntry] = []
        current_id = 1
        
        for input_path in input_paths:
            # Parse each file
            raw_entries = self._parser.parse_file(input_path)
            
            # Assign IDs starting from current_id
            for raw_entry in raw_entries:
                entry = raw_entry.to_faq_entry(current_id)
                all_entries.append(entry)
                current_id += 1
        
        # Generate and write
        code = self._generator.generate_code(all_entries, variable_name)
        self._generator.write_to_file(all_entries, output_path, variable_name)
        
        return code
    
    def _assign_ids_and_validate(
        self,
        raw_entries: list[RawFAQEntry],
    ) -> list[FAQEntry]:
        """Assign sequential IDs to entries and validate.
        
        Args:
            raw_entries: List of RawFAQEntry objects
            
        Returns:
            List of validated FAQEntry objects with IDs
            
        Raises:
            FAQValidationError: If any entry fails validation
            
        Complexity: O(n * k) where n = entries, k = avg entry size
        """
        entries: list[FAQEntry] = []
        
        for i, raw_entry in enumerate(raw_entries):
            try:
                # Pydantic validation happens in to_faq_entry()
                entry = raw_entry.to_faq_entry(entry_id=i + 1)
                entries.append(entry)
            except Exception as e:
                raise FAQValidationError(
                    f"Validation failed: {e}",
                    entry_index=i,
                ) from e
        
        return entries
