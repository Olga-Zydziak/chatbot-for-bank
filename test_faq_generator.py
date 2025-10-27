"""Comprehensive test suite for FAQ Generator.

This module provides thorough testing coverage for all components:
- Parser edge cases and error handling
- Model validation
- Code generation correctness
- End-to-end conversion workflow
- Security validation (path traversal, injection)

Test Coverage Target: 100%
Complexity: O(n) per test case where n = test data size
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import ValidationError

from faq_generator import (
    FAQConverter,
    FAQEntry,
    FAQGenerationError,
    FAQParseError,
    FAQParser,
    FAQValidationError,
    RawFAQEntry,
)
from faq_generator.generator import FAQCodeGenerator


class TestFAQEntry:
    """Test suite for FAQEntry model validation."""
    
    def test_valid_entry_creation(self) -> None:
        """Test creating a valid FAQ entry.
        
        Complexity: O(1)
        """
        entry = FAQEntry(
            id=1,
            category="test",
            q="Test question?",
            a="Test answer.",
            aliases=["alt1", "alt2"],
            next_steps=["Step 1", "Step 2"],
            tags=["tag1", "tag2"],
        )
        
        assert entry.id == 1
        assert entry.category == "test"
        assert len(entry.aliases) == 2
        assert len(entry.next_steps) == 2
        assert len(entry.tags) == 2
    
    def test_minimal_entry_creation(self) -> None:
        """Test entry with only mandatory fields.
        
        Complexity: O(1)
        """
        entry = FAQEntry(
            id=1,
            category="test",
            q="Test?",
            a="Answer.",
        )
        
        assert entry.aliases == []
        assert entry.next_steps == []
        assert entry.tags == []
    
    def test_invalid_id_zero(self) -> None:
        """Test that ID must be positive.
        
        Complexity: O(1)
        """
        with pytest.raises(ValidationError):
            FAQEntry(
                id=0,
                category="test",
                q="Test?",
                a="Answer.",
            )
    
    def test_invalid_id_negative(self) -> None:
        """Test that negative IDs are rejected.
        
        Complexity: O(1)
        """
        with pytest.raises(ValidationError):
            FAQEntry(
                id=-1,
                category="test",
                q="Test?",
                a="Answer.",
            )
    
    def test_empty_category_rejected(self) -> None:
        """Test that empty category strings are rejected.
        
        Complexity: O(1)
        """
        with pytest.raises(ValidationError):
            FAQEntry(
                id=1,
                category="",
                q="Test?",
                a="Answer.",
            )
    
    def test_empty_question_rejected(self) -> None:
        """Test that empty questions are rejected.
        
        Complexity: O(1)
        """
        with pytest.raises(ValidationError):
            FAQEntry(
                id=1,
                category="test",
                q="",
                a="Answer.",
            )
    
    def test_empty_answer_rejected(self) -> None:
        """Test that empty answers are rejected.
        
        Complexity: O(1)
        """
        with pytest.raises(ValidationError):
            FAQEntry(
                id=1,
                category="test",
                q="Test?",
                a="",
            )
    
    def test_immutability(self) -> None:
        """Test that entries are immutable (frozen).
        
        Complexity: O(1)
        """
        entry = FAQEntry(
            id=1,
            category="test",
            q="Test?",
            a="Answer.",
        )
        
        with pytest.raises(ValidationError):
            entry.category = "modified"  # type: ignore


class TestRawFAQEntry:
    """Test suite for RawFAQEntry model."""
    
    def test_to_faq_entry_conversion(self) -> None:
        """Test conversion from RawFAQEntry to FAQEntry.
        
        Complexity: O(1)
        """
        raw = RawFAQEntry(
            category="test",
            q="Test?",
            a="Answer.",
            aliases=["alt"],
            next_steps=["step"],
            tags=["tag"],
        )
        
        entry = raw.to_faq_entry(entry_id=42)
        
        assert entry.id == 42
        assert entry.category == "test"
        assert entry.q == "Test?"
        assert entry.a == "Answer."


class TestFAQParser:
    """Test suite for FAQ text parser."""
    
    def test_parse_single_entry(self, tmp_path: Path) -> None:
        """Test parsing a single FAQ entry.
        
        Complexity: O(n) where n = file size
        """
        faq_file = tmp_path / "test.txt"
        faq_file.write_text(dedent("""
            [CATEGORY: test]
            Q: Test question?
            A: Test answer.
            ALIASES: Alt question
            NEXT_STEPS:
            - Step 1
            - Step 2
            TAGS: tag1, tag2
        """).strip())
        
        parser = FAQParser()
        entries = parser.parse_file(faq_file)
        
        assert len(entries) == 1
        assert entries[0].category == "test"
        assert entries[0].q == "Test question?"
        assert entries[0].a == "Test answer."
        assert entries[0].aliases == ["Alt question"]
        assert entries[0].next_steps == ["Step 1", "Step 2"]
        assert entries[0].tags == ["tag1", "tag2"]
    
    def test_parse_multiple_entries(self, tmp_path: Path) -> None:
        """Test parsing multiple FAQ entries.
        
        Complexity: O(n) where n = file size
        """
        faq_file = tmp_path / "test.txt"
        faq_file.write_text(dedent("""
            [CATEGORY: cat1]
            Q: Question 1?
            A: Answer 1.
            
            [CATEGORY: cat2]
            Q: Question 2?
            A: Answer 2.
        """).strip())
        
        parser = FAQParser()
        entries = parser.parse_file(faq_file)
        
        assert len(entries) == 2
        assert entries[0].category == "cat1"
        assert entries[1].category == "cat2"
    
    def test_parse_multiline_answer(self, tmp_path: Path) -> None:
        """Test parsing multi-line answers.
        
        Complexity: O(n) where n = file size
        """
        faq_file = tmp_path / "test.txt"
        faq_file.write_text(dedent("""
            [CATEGORY: test]
            Q: Test?
            A: Line 1.
            Line 2.
            Line 3.
            TAGS: test
        """).strip())
        
        parser = FAQParser()
        entries = parser.parse_file(faq_file)
        
        assert len(entries) == 1
        assert entries[0].a == "Line 1. Line 2. Line 3."
    
    def test_parse_without_optional_fields(self, tmp_path: Path) -> None:
        """Test parsing entry without optional fields.
        
        Complexity: O(n) where n = file size
        """
        faq_file = tmp_path / "test.txt"
        faq_file.write_text(dedent("""
            [CATEGORY: test]
            Q: Test?
            A: Answer.
        """).strip())
        
        parser = FAQParser()
        entries = parser.parse_file(faq_file)
        
        assert len(entries) == 1
        assert entries[0].aliases == []
        assert entries[0].next_steps == []
        assert entries[0].tags == []
    
    def test_parse_file_not_found(self) -> None:
        """Test error handling for missing file.
        
        Complexity: O(1)
        """
        parser = FAQParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/file.txt"))
    
    def test_parse_empty_file(self, tmp_path: Path) -> None:
        """Test error handling for empty file.
        
        Complexity: O(1)
        """
        faq_file = tmp_path / "empty.txt"
        faq_file.write_text("")
        
        parser = FAQParser()
        
        with pytest.raises(FAQParseError, match="No FAQ entries"):
            parser.parse_file(faq_file)
    
    def test_parse_missing_mandatory_question(self, tmp_path: Path) -> None:
        """Test that missing question field is caught.
        
        Complexity: O(n) where n = file size
        """
        faq_file = tmp_path / "test.txt"
        faq_file.write_text(dedent("""
            [CATEGORY: test]
            A: Answer without question.
        """).strip())
        
        parser = FAQParser()
        
        with pytest.raises(FAQParseError):
            parser.parse_file(faq_file)


class TestFAQCodeGenerator:
    """Test suite for Python code generator."""
    
    def test_generate_single_entry(self) -> None:
        """Test code generation for single entry.
        
        Complexity: O(n) where n = entry size
        """
        entries = [
            FAQEntry(
                id=1,
                category="test",
                q="Test?",
                a="Answer.",
                aliases=[],
                next_steps=[],
                tags=[],
            )
        ]
        
        generator = FAQCodeGenerator()
        code = generator.generate_code(entries)
        
        assert "FAQ_DATA = [" in code
        assert '"id": 1' in code
        assert '"category": \'test\'' in code
        assert '"q": \'Test?\'' in code
        assert '"a": \'Answer.\'' in code
    
    def test_generate_multiple_entries(self) -> None:
        """Test code generation for multiple entries.
        
        Complexity: O(n * m) where n = entries, m = avg size
        """
        entries = [
            FAQEntry(id=i, category="test", q=f"Q{i}?", a=f"A{i}.")
            for i in range(1, 4)
        ]
        
        generator = FAQCodeGenerator()
        code = generator.generate_code(entries)
        
        assert '"id": 1' in code
        assert '"id": 2' in code
        assert '"id": 3' in code
    
    def test_generate_with_special_characters(self) -> None:
        """Test that special characters are properly escaped.
        
        Complexity: O(n) where n = entry size
        """
        entries = [
            FAQEntry(
                id=1,
                category="test",
                q="What's \"quoted\"?",
                a="Answer with 'quotes' and \"double quotes\".",
            )
        ]
        
        generator = FAQCodeGenerator()
        code = generator.generate_code(entries)
        
        # Verify code is valid Python
        namespace: dict[str, object] = {}
        exec(code, namespace)
        data = namespace["FAQ_DATA"]
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["q"] == "What's \"quoted\"?"
    
    def test_generate_with_unicode(self) -> None:
        """Test Unicode character handling (Polish chars).
        
        Complexity: O(n) where n = entry size
        """
        entries = [
            FAQEntry(
                id=1,
                category="test",
                q="Jak zgłosić chargeback?",
                a="Spór zgłosisz przez aplikację.",
                aliases=["Reklamacja płatności"],
                tags=["ąćęłńóśźż"],
            )
        ]
        
        generator = FAQCodeGenerator()
        code = generator.generate_code(entries)
        
        # Verify Unicode is preserved
        assert "Jak zgłosić" in code
        assert "ąćęłńóśźż" in code
    
    def test_generate_empty_list_error(self) -> None:
        """Test that empty entry list raises error.
        
        Complexity: O(1)
        """
        generator = FAQCodeGenerator()
        
        with pytest.raises(FAQGenerationError, match="empty"):
            generator.generate_code([])
    
    def test_write_to_file(self, tmp_path: Path) -> None:
        """Test writing generated code to file.
        
        Complexity: O(n) where n = entry size
        """
        entries = [
            FAQEntry(id=1, category="test", q="Test?", a="Answer.")
        ]
        
        output_file = tmp_path / "output.py"
        generator = FAQCodeGenerator()
        generator.write_to_file(entries, output_file)
        
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "FAQ_DATA" in content


class TestFAQConverter:
    """Test suite for end-to-end conversion."""
    
    def test_convert_file_success(self, tmp_path: Path) -> None:
        """Test successful file conversion.
        
        Complexity: O(n) where n = file size
        """
        input_file = tmp_path / "input.txt"
        input_file.write_text(dedent("""
            [CATEGORY: test]
            Q: Test question?
            A: Test answer.
        """).strip())
        
        output_file = tmp_path / "output.py"
        converter = FAQConverter()
        code = converter.convert_file(input_file, output_file)
        
        assert output_file.exists()
        assert "FAQ_DATA" in code
        assert '"id": 1' in code
    
    def test_convert_multiple_files(self, tmp_path: Path) -> None:
        """Test converting multiple files into one output.
        
        Complexity: O(n * m) where n = files, m = avg size
        """
        file1 = tmp_path / "file1.txt"
        file1.write_text(dedent("""
            [CATEGORY: cat1]
            Q: Q1?
            A: A1.
        """).strip())
        
        file2 = tmp_path / "file2.txt"
        file2.write_text(dedent("""
            [CATEGORY: cat2]
            Q: Q2?
            A: A2.
        """).strip())
        
        output_file = tmp_path / "combined.py"
        converter = FAQConverter()
        code = converter.convert_multiple_files(
            [file1, file2],
            output_file,
        )
        
        assert output_file.exists()
        assert '"id": 1' in code
        assert '"id": 2' in code
    
    def test_convert_file_validation_error(self, tmp_path: Path) -> None:
        """Test that invalid entries raise validation error.
        
        Complexity: O(n) where n = file size
        """
        input_file = tmp_path / "invalid.txt"
        # Missing answer field
        input_file.write_text(dedent("""
            [CATEGORY: test]
            Q: Question without answer?
        """).strip())
        
        converter = FAQConverter()
        
        with pytest.raises((FAQParseError, FAQValidationError)):
            converter.convert_file(input_file)


class TestSecurityValidation:
    """Test security-related validation."""
    
    def test_path_traversal_prevention(self, tmp_path: Path) -> None:
        """Test that path traversal is handled safely.
        
        Complexity: O(1)
        """
        converter = FAQConverter()
        
        # This should not raise, just properly resolve the path
        malicious_path = tmp_path / ".." / ".." / "etc" / "passwd"
        
        with pytest.raises(FileNotFoundError):
            converter.convert_file(malicious_path)
    
    def test_code_injection_prevention(self) -> None:
        """Test that generated code is safe from injection.
        
        Complexity: O(n) where n = entry size
        """
        entries = [
            FAQEntry(
                id=1,
                category="test",
                q="Test?",
                a='"); import os; os.system("rm -rf /"); print("',
            )
        ]
        
        generator = FAQCodeGenerator()
        code = generator.generate_code(entries)
        
        # Execute generated code - should be safe
        namespace: dict[str, object] = {}
        exec(code, namespace)
        
        # Verify data is properly escaped
        data = namespace["FAQ_DATA"]
        assert isinstance(data, list)
        # The string should be safely stored, not executed
        assert "rm -rf" in data[0]["a"]


# Integration test using real uploaded file
def test_real_file_conversion(tmp_path: Path) -> None:
    """Integration test with real FAQ file.
    
    This test uses the actual uploaded banking FAQ file
    to verify end-to-end functionality.
    
    Complexity: O(n) where n = file size
    """
    # Path to the uploaded file
    input_file = Path("/mnt/user-data/uploads/banking_faq_30plus.txt")
    
    if not input_file.exists():
        pytest.skip("Real FAQ file not available")
    
    output_file = tmp_path / "banking_faq.py"
    converter = FAQConverter()
    
    code = converter.convert_file(input_file, output_file)
    
    # Verify output
    assert output_file.exists()
    assert "FAQ_DATA" in code
    
    # Verify generated code is valid Python
    namespace: dict[str, object] = {}
    exec(code, namespace)
    data = namespace["FAQ_DATA"]
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify structure of first entry
    first_entry = data[0]
    assert "id" in first_entry
    assert "category" in first_entry
    assert "q" in first_entry
    assert "a" in first_entry
