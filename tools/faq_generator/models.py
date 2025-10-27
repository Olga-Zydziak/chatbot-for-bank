"""Domain models for FAQ data structure.

This module defines the core domain models using Pydantic for strict validation
and type safety. All models are immutable (frozen) to prevent accidental mutations.

Complexity Analysis:
    - Validation: O(n) where n = number of fields
    - Serialization: O(n) where n = dictionary size
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class FAQEntry(BaseModel):
    """Single FAQ entry with complete validation.
    
    This model represents a parsed FAQ entry from the text file format.
    All string fields are validated for non-empty content, and lists
    default to empty rather than None for simplicity.
    
    Attributes:
        id: Unique positive integer identifier
        category: FAQ category (e.g., 'chargeback', 'card')
        q: The question text
        aliases: Alternative phrasings of the question
        a: The answer text
        next_steps: Ordered list of actionable steps
        tags: Searchable tags for categorization
    
    Complexity:
        Creation: O(k) where k = total number of characters across all fields
        Validation: O(k) for string length checks
    """
    
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        validate_assignment=True,
    )
    
    id: Annotated[int, Field(gt=0, description="Unique FAQ entry ID")]
    category: Annotated[
        str, 
        Field(min_length=1, max_length=64, description="FAQ category")
    ]
    q: Annotated[
        str, 
        Field(min_length=1, max_length=500, description="Question text")
    ]
    aliases: Annotated[
        list[str], 
        Field(default_factory=list, description="Alternative question phrasings")
    ]
    a: Annotated[
        str, 
        Field(min_length=1, max_length=2000, description="Answer text")
    ]
    next_steps: Annotated[
        list[str], 
        Field(default_factory=list, description="Actionable next steps")
    ]
    tags: Annotated[
        list[str], 
        Field(default_factory=list, description="Search tags")
    ]


class RawFAQEntry(BaseModel):
    """Raw parsed FAQ entry before ID assignment.
    
    This is an intermediate representation used during parsing, before
    the final ID is assigned. All fields except `id` are identical to FAQEntry.
    
    Complexity: O(k) where k = total field content size
    """
    
    model_config = ConfigDict(
        frozen=True,
        strict=True,
    )
    
    category: str = Field(min_length=1)
    q: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    a: str = Field(min_length=1)
    next_steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    
    def to_faq_entry(self, entry_id: int) -> FAQEntry:
        """Convert to FAQEntry with assigned ID.
        
        Args:
            entry_id: Unique positive integer ID
            
        Returns:
            Validated FAQEntry with ID
            
        Complexity: O(k) where k = size of all fields
        """
        return FAQEntry(
            id=entry_id,
            category=self.category,
            q=self.q,
            aliases=self.aliases,
            a=self.a,
            next_steps=self.next_steps,
            tags=self.tags,
        )
