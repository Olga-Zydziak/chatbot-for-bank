#!/usr/bin/env python3
"""CLI interface for FAQ Generator.

This script provides a command-line interface for converting FAQ text files
to Python code. It supports single or multiple input files and includes
comprehensive error handling and user feedback.

Usage:
    python generate_faq.py input.txt -o output.py
    python generate_faq.py file1.txt file2.txt -o combined.py
    python generate_faq.py input.txt  # Prints to stdout

Complexity: O(n) where n = total input size
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import NoReturn

from faq_generator import FAQConverter, FAQGeneratorError


def parse_arguments() -> Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
        
    Complexity: O(1)
    """
    parser = ArgumentParser(
        description="Convert FAQ text files to Python code",
        epilog="Example: %(prog)s input.txt -o output.py",
    )
    
    parser.add_argument(
        "input_files",
        type=Path,
        nargs="+",
        metavar="INPUT",
        help="FAQ text file(s) to convert",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="Output Python file (default: print to stdout)",
    )
    
    parser.add_argument(
        "-v",
        "--variable",
        type=str,
        default="FAQ_DATA",
        metavar="NAME",
        help="Python variable name (default: FAQ_DATA)",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    return parser.parse_args()


def print_success(
    input_files: list[Path],
    output_path: Path | None,
    entry_count: int,
) -> None:
    """Print success message with summary.
    
    Args:
        input_files: List of processed input files
        output_path: Output file path (None if stdout)
        entry_count: Number of entries generated
        
    Complexity: O(1)
    """
    print("✅ Conversion successful!", file=sys.stderr)
    print(f"   Processed files: {len(input_files)}", file=sys.stderr)
    print(f"   Generated entries: {entry_count}", file=sys.stderr)
    
    if output_path:
        print(f"   Output written to: {output_path}", file=sys.stderr)
    else:
        print("   Output sent to stdout", file=sys.stderr)


def print_error(error: Exception) -> None:
    """Print error message with context.
    
    Args:
        error: Exception that occurred
        
    Complexity: O(1)
    """
    print(f"❌ Error: {error}", file=sys.stderr)
    
    # Add helpful hints for common errors
    if isinstance(error, FileNotFoundError):
        print("   Hint: Check that the input file exists", file=sys.stderr)
    elif "Validation" in str(type(error).__name__):
        print("   Hint: Check FAQ entry format and required fields", file=sys.stderr)
    elif "Parse" in str(type(error).__name__):
        print("   Hint: Verify text file format (CATEGORY, Q:, A:, etc.)", file=sys.stderr)


def exit_with_error(message: str, code: int = 1) -> NoReturn:
    """Print error and exit with status code.
    
    Args:
        message: Error message
        code: Exit status code
        
    Complexity: O(1)
    """
    print(f"❌ {message}", file=sys.stderr)
    sys.exit(code)


def main() -> None:
    """Main entry point for CLI.
    
    Orchestrates the conversion process with proper error handling
    and user feedback.
    
    Complexity: O(n * m) where n = files, m = avg file size
    """
    args = parse_arguments()
    
    # Validate input files exist
    for input_file in args.input_files:
        if not input_file.exists():
            exit_with_error(f"Input file not found: {input_file}")
    
    # Create converter
    converter = FAQConverter()
    
    try:
        # Convert single or multiple files
        if len(args.input_files) == 1:
            code = converter.convert_file(
                input_path=args.input_files[0],
                output_path=args.output,
                variable_name=args.variable,
            )
        else:
            code = converter.convert_multiple_files(
                input_paths=args.input_files,
                output_path=args.output or Path("faq_data.py"),
                variable_name=args.variable,
            )
        
        # Output to stdout if no output file specified
        if args.output is None:
            print(code)
        
        # Count entries for summary
        entry_count = code.count('"id":')
        
        # Print success message to stderr (so stdout is clean)
        print_success(args.input_files, args.output, entry_count)
        
    except FAQGeneratorError as e:
        print_error(e)
        sys.exit(1)
    
    except KeyboardInterrupt:
        exit_with_error("Interrupted by user", code=130)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        print("   Please report this as a bug", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
