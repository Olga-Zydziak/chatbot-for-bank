#!/usr/bin/env python3
"""Example usage of FAQ Generator.

This script demonstrates how to use the FAQ Generator both via CLI
and programmatically through the Python API.
"""

from pathlib import Path
from faq_generator import FAQConverter, FAQParser, FAQCodeGenerator

def example_cli_usage():
    """Examples of CLI usage (run these in your terminal)."""
    print("=" * 80)
    print("CLI USAGE EXAMPLES")
    print("=" * 80)
    print()
    
    examples = [
        ("Convert single file to Python code:",
         "python generate_faq.py input.txt -o output.py"),
        
        ("Convert multiple files into one:",
         "python generate_faq.py file1.txt file2.txt -o combined.py"),
        
        ("Print to stdout (for piping):",
         "python generate_faq.py input.txt"),
        
        ("Custom variable name:",
         "python generate_faq.py input.txt -o data.py -v MY_FAQ_DATA"),
        
        ("Real banking FAQ example:",
         "python generate_faq.py banking_faq_30plus.txt -o banking_faq_data.py"),
    ]
    
    for title, command in examples:
        print(f"# {title}")
        print(f"$ {command}")
        print()


def example_api_usage():
    """Examples of Python API usage."""
    print("=" * 80)
    print("PYTHON API USAGE EXAMPLES")
    print("=" * 80)
    print()
    
    print("# Example 1: Simple file conversion")
    print("""
from pathlib import Path
from faq_generator import FAQConverter

converter = FAQConverter()
code = converter.convert_file(
    input_path=Path("faq.txt"),
    output_path=Path("faq_data.py"),
    variable_name="FAQ_DATA"
)

print(f"Generated {len(code)} characters of code")
    """)
    
    print("\n# Example 2: Convert multiple files")
    print("""
converter = FAQConverter()
code = converter.convert_multiple_files(
    input_paths=[
        Path("faq_chargeback.txt"),
        Path("faq_cards.txt"),
        Path("faq_transfers.txt")
    ],
    output_path=Path("all_faq.py")
)
    """)
    
    print("\n# Example 3: Custom components")
    print("""
from faq_generator import FAQParser, FAQCodeGenerator

# Use custom parser and generator
parser = FAQParser()
generator = FAQCodeGenerator(indent_size=2)  # 2-space indent

converter = FAQConverter(parser=parser, generator=generator)
code = converter.convert_file(Path("input.txt"))
    """)
    
    print("\n# Example 4: Error handling")
    print("""
from faq_generator import (
    FAQConverter,
    FAQParseError,
    FAQValidationError,
    FAQGenerationError
)

converter = FAQConverter()

try:
    code = converter.convert_file(Path("faq.txt"), Path("output.py"))
    print("✅ Conversion successful!")
    
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
    
except FAQParseError as e:
    print(f"❌ Parse error: {e}")
    # e.line_no contains the line number where error occurred
    
except FAQValidationError as e:
    print(f"❌ Validation error: {e}")
    # e.entry_index contains the entry that failed
    
except FAQGenerationError as e:
    print(f"❌ Generation error: {e}")
    """)


def example_output_format():
    """Show example input and output format."""
    print("=" * 80)
    print("INPUT/OUTPUT FORMAT EXAMPLE")
    print("=" * 80)
    print()
    
    print("# INPUT FILE (faq.txt):")
    print("""
[CATEGORY: card]
Q: Jak zmienić PIN do karty?
A: PIN zmienisz w aplikacji mobilnej: przejdź do Karty → Ustawienia → Zmień PIN.
ALIASES: Zmiana PIN, Reset PIN do karty
NEXT_STEPS:
- Aplikacja → Karty → Wybierz kartę
- Kliknij 'Ustawienia' → 'Zmień PIN'
- Wprowadź nowy PIN (4 cyfry)
TAGS: karta, PIN, bezpieczeństwo
    """)
    
    print("\n# OUTPUT FILE (faq_data.py):")
    print("""
FAQ_DATA = [
    {
        "id": 1,
        "category": 'card',
        "q": 'Jak zmienić PIN do karty?',
        "aliases": [
            'Zmiana PIN',
            'Reset PIN do karty'
        ],
        "a": 'PIN zmienisz w aplikacji mobilnej: przejdź do Karty → Ustawienia → Zmień PIN.',
        "next_steps": [
            'Aplikacja → Karty → Wybierz kartę',
            "Kliknij 'Ustawienia' → 'Zmień PIN'",
            'Wprowadź nowy PIN (4 cyfry)'
        ],
        "tags": [
            'karta',
            'PIN',
            'bezpieczeństwo'
        ]
    }
]
    """)


if __name__ == "__main__":
    example_cli_usage()
    example_api_usage()
    example_output_format()
    
    print("=" * 80)
    print("For more information, see README.md")
    print("=" * 80)
