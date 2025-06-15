"""Enhanced text manipulation operations with improved error handling."""
import re
from typing import List, Dict, Optional, Union, Pattern, Callable, Match, Any
import logging
from dataclasses import dataclass, field
from enum import Enum, auto

# Configure logger
logger = logging.getLogger("lawglance.text_operations")

# Define constants to replace magic numbers
MAX_REPLACEMENT_ATTEMPTS = 100  # Safety limit for replacement operations
DEFAULT_BUFFER_SIZE = 1024  # Buffer size for processing
DEFAULT_ENCODING = "utf-8"  # Default file encoding


class ReplacementError(Exception):
    """Exception raised for errors during text replacement."""
    pass


class OperationStatus(Enum):
    """Enumeration for operation status."""
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class TextReplacement:
    """Represents a text replacement operation."""
    old_text: str
    new_text: str
    positions: List[int] = field(default_factory=list)
    was_regex: bool = False
    replacements_made: int = 0
    status: OperationStatus = OperationStatus.SUCCESS
    message: Optional[str] = None
    
    def __repr__(self) -> str:
        """String representation of text replacement."""
        status_str = self.status.name if self.status else "UNKNOWN"
        return (f"TextReplacement('{self.old_text}' → '{self.new_text}', "
                f"count={self.replacements_made}, status={status_str})")


class RegexTextReplacer:
    """Enhanced utility for performing regex-based text replacements."""
    
    def __init__(self, max_replacements: int = MAX_REPLACEMENT_ATTEMPTS):
        """
        Initialize the regex text replacer.
        
        Args:
            max_replacements: Maximum number of replacements to prevent infinite loops
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_operation: Optional[TextReplacement] = None
        self.max_replacements = max_replacements
    
    def __str__(self) -> str:
        """Return string representation of the text replacer."""
        if self.last_operation:
            return f"RegexTextReplacer(last={self.last_operation})"
        return "RegexTextReplacer()"
    
    def replace_with_regex(self, text: str, pattern: Union[str, Pattern], 
                           replacement: Union[str, Callable]) -> str:
        """
        Replace text using regex pattern.
        
        Args:
            text: Original text
            pattern: Regular expression pattern (string or compiled)
            replacement: Replacement string or function
            
        Returns:
            Text with replacements applied
            
        Raises:
            ReplacementError: If an error occurs during replacement
            ValueError: If invalid pattern or replacement is provided
        """
        if not text:
            self.logger.warning("Empty text provided for replacement")
            self._record_operation("", "", [], True, 0, 
                                   OperationStatus.WARNING, "Empty text provided")
            return text
            
        if not pattern:
            raise ValueError("Pattern cannot be empty")
            
        try:
            # Compile pattern if it's a string
            if isinstance(pattern, str):
                try:
                    compiled_pattern = re.compile(pattern)
                except re.error as e:
                    raise ValueError(f"Invalid regular expression pattern: {e}")
            else:
                compiled_pattern = pattern
                
            # Find original positions before replacement
            positions = []
            for match in compiled_pattern.finditer(text):
                positions.append(match.start())
            
            # Check if we might exceed max replacements
            if len(positions) > self.max_replacements:
                self.logger.warning(
                    f"Pattern matches {len(positions)} positions, which exceeds "
                    f"max_replacements ({self.max_replacements}). Proceeding anyway."
                )
            
            # Perform replacement
            result = compiled_pattern.sub(replacement, text)
            
            # Count replacements by comparing occurrences
            original_count = len(positions)
            result_count = len(list(compiled_pattern.finditer(result)))
            replacements_made = original_count - result_count
            
            # Store operation details
            pattern_str = pattern if isinstance(pattern, str) else pattern.pattern
            replacement_str = replacement if isinstance(replacement, str) else "<function>"
            
            # Record the operation
            self._record_operation(
                pattern_str, 
                replacement_str, 
                positions, 
                True, 
                replacements_made,
                OperationStatus.SUCCESS
            )
            
            self.logger.debug(f"Made {replacements_made} replacements using pattern {pattern_str}")
            return result
            
        except re.error as e:
            error_msg = f"Regular expression error: {e}"
            self.logger.error(error_msg)
            self._record_operation(
                pattern if isinstance(pattern, str) else pattern.pattern,
                replacement if isinstance(replacement, str) else "<function>",
                [],
                True,
                0,
                OperationStatus.ERROR,
                error_msg
            )
            raise ReplacementError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during regex replacement: {e}"
            self.logger.error(error_msg)
            self._record_operation(
                pattern if isinstance(pattern, str) else pattern.pattern,
                replacement if isinstance(replacement, str) else "<function>",
                [],
                True,
                0,
                OperationStatus.ERROR,
                error_msg
            )
            raise ReplacementError(error_msg) from e
    
    def replace_case_preserving(self, text: str, old_text: str, new_text: str) -> str:
        """
        Replace text while preserving case patterns.
        
        Args:
            text: Original text
            old_text: Text to replace
            new_text: Replacement text
            
        Returns:
            Text with replacements applied, preserving case
            
        Raises:
            ValueError: If old_text or new_text is empty
        """
        if not text:
            return text
            
        if not old_text:
            raise ValueError("Search text cannot be empty")
            
        if new_text is None:  # Allow empty replacement string
            new_text = ""
        
        # Find positions before replacement
        positions = self.find_positions(text, old_text)
        
        # Define case-preserving replacement function
        def _replacement_function(match: Match) -> str:
            matched_text = match.group(0)
            
            # If all uppercase
            if matched_text.isupper():
                return new_text.upper()
            # If title case (first letter of each word is capitalized)
            elif matched_text.istitle():
                return new_text.title()
            # If only first letter capitalized
            elif matched_text and matched_text[0].isupper() and matched_text[1:].lower() == matched_text[1:]:
                return new_text[0].upper() + new_text[1:].lower() if new_text else ""
            # Otherwise keep as is
            else:
                return new_text
        
        try:
            # Create pattern that ignores case for finding old_text
            pattern = re.compile(re.escape(old_text), re.IGNORECASE)
            result = pattern.sub(_replacement_function, text)
            
            # Count replacements
            replacements_made = len(positions)
            
            # Record the operation
            self._record_operation(
                old_text, 
                new_text, 
                positions, 
                False, 
                replacements_made,
                OperationStatus.SUCCESS
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error in case-preserving replacement: {e}"
            self.logger.error(error_msg)
            self._record_operation(
                old_text,
                new_text,
                positions,
                False,
                0,
                OperationStatus.ERROR,
                error_msg
            )
            raise ReplacementError(error_msg) from e
    
    @staticmethod
    def find_positions(text: str, search_text: str) -> List[int]:
        """
        Find all positions of search_text in text.
        
        Args:
            text: Text to search in
            search_text: Text to find
            
        Returns:
            List of start positions for each occurrence
            
        Raises:
            ValueError: If search_text is empty
        """
        if not text:
            return []
            
        if not search_text:
            raise ValueError("Search text cannot be empty")
            
        positions = []
        start = 0
        
        while start < len(text):
            start = text.find(search_text, start)
            if start == -1:
                break
            positions.append(start)
            start += len(search_text)  # Move past this occurrence
            
        return positions
    
    @staticmethod
    def replace_at_position(text: str, replacement: str, position: int, length: int) -> str:
        """
        Replace text at specific position.
        
        Args:
            text: Original text
            replacement: Replacement text
            position: Start position
            length: Length of text to replace
            
        Returns:
            Text with replacement applied at specific position
        """
        if position < 0 or position >= len(text):
            logger.error(f"Invalid position: {position}")
            return text
            
        return text[:position] + replacement + text[position + length:]

class TextProcessor:
    """Text processor for advanced text operations."""
    
    def __init__(self):
        """Initialize the text processor."""
        self.replacer = RegexTextReplacer()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Trim leading/trailing whitespace from each line
        text = '\n'.join(line.strip() for line in text.splitlines())
        # Remove empty lines
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """
        Extract paragraphs from text.
        
        Args:
            text: Text to extract paragraphs from
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines (common paragraph separator)
        paragraphs = re.split(r'\n\s*\n', text)
        # Filter out empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]
    
    def detect_language(self, text: str) -> str:
        """
        Attempt to detect the language of the text.
        This is a simple implementation - for better results use a dedicated library.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (en, es, fr, etc.) or "unknown"
        """
        # Count common words in different languages
        english_words = ['the', 'and', 'of', 'to', 'in', 'that', 'it', 'with']
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un']
        french_words = ['le', 'la', 'de', 'et', 'à', 'en', 'un', 'une']
        
        text_lower = text.lower()
        
        en_count = sum(1 for word in english_words if f" {word} " in f" {text_lower} ")
        es_count = sum(1 for word in spanish_words if f" {word} " in f" {text_lower} ")
        fr_count = sum(1 for word in french_words if f" {word} " in f" {text_lower} ")
        
        if en_count > es_count and en_count > fr_count:
            return "en"
        elif es_count > en_count and es_count > fr_count:
            return "es"
        elif fr_count > en_count and fr_count > es_count:
            return "fr"
        else:
            return "unknown"

def perform_operation(data):
    """Perform some operation on the data."""
    try:
        # Placeholder for operation logic
        logger.info("Performing operation on data.")
        # Simulate operation
        result = data * 2  # Example operation
        logger.info("Operation completed successfully.")
        return result
    except ValueError as e:
        logger.error("Value error occurred: %s", e)
        return None
    except Exception as e:
        logger.error("An error occurred: %s", e)
        return None

def another_function(arg1, arg2):
    """Another function that does something."""
    try:
        # Placeholder for another function logic
        logger.info("Processing with arg1: %s and arg2: %s", arg1, arg2)
        # Simulate processing
        return arg1 + arg2
    except TypeError as e:
        logger.error("Type error occurred: %s", e)
        return None
    except Exception as e:
        logger.error("An error occurred: %s", e)
        return None
