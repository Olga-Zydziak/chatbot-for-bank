# FAQ Generator

**Professional-grade Python tool for converting structured text FAQ files into Python code.**

## Features

- ✅ **Robust Parser**: State machine-based parser handles multi-line answers and optional sections
- ✅ **Type Safety**: 100% strict typing with Pydantic validation
- ✅ **Security**: Built-in protection against path traversal and code injection
- ✅ **Unicode Support**: Full Polish character support (and other UTF-8)
- ✅ **Error Handling**: Detailed error messages with line numbers
- ✅ **Clean Code**: SOLID principles, zero technical debt

## Installation

```bash
pip install pydantic>=2.0.0
```

## Usage

### CLI

```bash
# Convert single file
python generate_faq.py input.txt -o output.py

# Convert multiple files into one
python generate_faq.py file1.txt file2.txt -o combined.py

# Print to stdout
python generate_faq.py input.txt

# Custom variable name
python generate_faq.py input.txt -o output.py -v MY_FAQ_DATA
```

### Python API

```python
from pathlib import Path
from faq_generator import FAQConverter

# Simple conversion
converter = FAQConverter()
code = converter.convert_file(
    input_path=Path("faq.txt"),
    output_path=Path("faq_data.py")
)

# Multiple files
code = converter.convert_multiple_files(
    input_paths=[Path("faq1.txt"), Path("faq2.txt")],
    output_path=Path("combined.py")
)
```

## Input Format

```text
[CATEGORY: chargeback]
Q: Co to jest chargeback?
A: Chargeback to proces zwrotu środków dla posiadacza karty.
ALIASES: Reklamacja płatności, Spór transakcja
NEXT_STEPS:
- Zgromadź dowody transakcji
- Otwórz aplikację
- Kliknij 'Zgłoś spór'
TAGS: chargeback, reklamacja, karta
```

### Format Rules

- **CATEGORY**: Required - category name in square brackets
- **Q:** Required - the question text
- **A:** Required - the answer (can be multi-line)
- **ALIASES:** Optional - comma-separated alternative phrasings
- **NEXT_STEPS:** Optional - bullet list with `-` or `•`
- **TAGS:** Optional - comma-separated tags

## Output Format

```python
FAQ_DATA = [
    {
        "id": 1,
        "category": "chargeback",
        "q": "Co to jest chargeback?",
        "aliases": [
            "Reklamacja płatności",
            "Spór transakcja"
        ],
        "a": "Chargeback to proces zwrotu środków...",
        "next_steps": [
            "Zgromadź dowody transakcji",
            "Otwórz aplikację",
            "Kliknij 'Zgłoś spór'"
        ],
        "tags": ["chargeback", "reklamacja", "karta"]
    },
    # ...
]
```

## Testing

```bash
pytest test_faq_generator.py -v
```

## Architecture

```
faq_generator/
├── __init__.py          # Public API
├── models.py            # Pydantic domain models
├── parser.py            # State machine parser
├── generator.py         # Python code generator
├── converter.py         # High-level service
└── exceptions.py        # Custom exception hierarchy
```

## Complexity Analysis

- **Parsing**: O(n) where n = file size (single-pass)
- **Validation**: O(m * k) where m = entries, k = avg entry size
- **Generation**: O(m * k) where m = entries, k = avg field count
- **Memory**: O(m) where m = number of entries

## Example: Banking FAQ

```bash
# Convert the banking FAQ file
python generate_faq.py banking_faq_30plus.txt -o banking_faq_data.py

# Result: 32 entries converted in <1 second
✅ Conversion successful!
   Processed files: 1
   Generated entries: 32
   Output written to: banking_faq_data.py
```

## Author

**Principal Systems Architect (L10)**  
Python 3.10+  
License: MIT

## Philosophy

This tool embodies Software Craftsmanship principles:
- **Simplicity First**: Minimal code, maximum clarity
- **Type Safety**: 100% mypy-strict compliant
- **Zero Technical Debt**: Clean Architecture, SOLID principles
- **Production Ready**: Comprehensive tests, security validation
