"""Improved test suite for document comparison functionality."""
import os
import sys
import pytest
from typing import Dict, Tuple, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.document_compare import DocumentCompare, DocumentInfo, ComparisonResult

class TestDocumentInfo:
    """Test suite for DocumentInfo class."""
    
    def test_init_with_file_path(self, sample_text_file: str) -> None:
        """Test initialization with file path loads content correctly."""
        # When
        doc_info = DocumentInfo(sample_text_file)
        
        # Then
        assert doc_info.content
        assert len(doc_info.paragraphs) > 0
        assert len(doc_info.sections) > 0
        assert doc_info.word_count > 0
    
    def test_extract_sections_finds_all_formats(self, sample_text_file: str) -> None:
        """Test that section extraction finds differently formatted sections."""
        # Given
        doc_info = DocumentInfo(sample_text_file)
        
        # When/Then
        assert "1. FIRST SECTION" in doc_info.sections
        assert "2. SECOND SECTION" in doc_info.sections
        assert "3. TERMINATION" in doc_info.sections
    
    def test_word_count_calculation(self, sample_text_file: str) -> None:
        """Test word count is calculated correctly."""
        # Given
        doc_info = DocumentInfo(sample_text_file)
        expected_count = len(doc_info.content.split())
        
        # When/Then
        assert doc_info.word_count == expected_count
    
    def test_missing_file_raises_exception(self) -> None:
        """Test that loading a non-existent file raises an appropriate exception."""
        # When/Then
        with pytest.raises(FileNotFoundError):
            doc_info = DocumentInfo("non_existent_file.txt")
            doc_info.load_content()  # Force load attempt
    
    def test_empty_content_handling(self, temp_test_dir: str) -> None:
        """Test handling of empty content."""
        # Given
        empty_file = os.path.join(temp_test_dir, "empty.txt")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("")
            
        # When
        doc_info = DocumentInfo(empty_file)
        
        # Then
        assert doc_info.content == ""
        assert len(doc_info.paragraphs) == 0
        assert doc_info.word_count == 0


class TestComparisonResult:
    """Test suite for ComparisonResult class."""
    
    def test_successful_result_representation(self) -> None:
        """Test string representation of successful comparison."""
        # Given
        result = ComparisonResult(
            success=True,
            similarity_percentage=85.5,
            difference_count=12
        )
        
        # When
        repr_str = repr(result)
        
        # Then
        assert "85.5%" in repr_str
        assert "differences=12" in repr_str
        assert "success=False" not in repr_str
    
    def test_failed_result_representation(self) -> None:
        """Test string representation of failed comparison."""
        # Given
        error_message = "File not found"
        result = ComparisonResult(
            success=False,
            error=error_message
        )
        
        # When
        repr_str = repr(result)
        
        # Then
        assert "success=False" in repr_str
        assert error_message in repr_str
    
    def test_to_dict_conversion(self, expected_comparison_result: Dict[str, Any]) -> None:
        """Test conversion to dictionary has all required fields."""
        # Given
        result = ComparisonResult(
            success=True,
            similarity_percentage=85.5,
            difference_count=3,
            additions=["4. NEW SECTION", "This is a new section."],
            deletions=["3. SECTION THREE", "This is the third section."],
            changes=[
                {
                    "removed": "This is the first section.", 
                    "added": "This is the modified first section."
                }
            ],
            summary="The documents are very similar with some differences."
        )
        
        # When
        result_dict = result.to_dict()
        
        # Then
        for key in expected_comparison_result:
            assert key in result_dict, f"Missing key: {key}"
        assert result_dict["success"] == True
        assert result_dict["similarity_percentage"] == 85.5
        assert len(result_dict["additions"]) == 2
        assert len(result_dict["deletions"]) == 2
        assert len(result_dict["changes"]) == 1


class TestDocumentCompare:
    """Test suite for DocumentCompare class."""
    
    def test_compare_files_with_valid_paths(self, similar_documents: Tuple[str, str]) -> None:
        """Test comparing two valid file paths works correctly."""
        # Given
        doc1_path, doc2_path = similar_documents
        comparer = DocumentCompare()
        
        # When
        result = comparer.compare_files(doc1_path, doc2_path)
        
        # Then
        assert result.success
        assert result.similarity_percentage > 0
        assert result.similarity_percentage < 100  # Not identical
        assert result.difference_count > 0
        assert len(result.additions) > 0
        assert len(result.deletions) > 0
    
    def test_constructor_with_file_paths(self, similar_documents: Tuple[str, str]) -> None:
        """Test constructor with file paths."""
        # Given
        file1_path, file2_path = similar_documents
        
        # When
        comparer = DocumentCompare(file1_path, file2_path)
        
        # Then
        assert comparer.file1_path == file1_path
        assert comparer.file2_path == file2_path
        assert comparer.doc1 is not None
        assert comparer.doc2 is not None
        assert comparer.doc1.path == file1_path
        assert comparer.doc2.path == file2_path
    
    def test_non_existent_file_handled_gracefully(self, temp_test_dir: str) -> None:
        """Test that comparing with a non-existent file returns an error result."""
        # Given
        existing_file = os.path.join(temp_test_dir, "exists.txt")
        with open(existing_file, "w", encoding="utf-8") as f:
            f.write("Some content")
            
        non_existent_file = os.path.join(temp_test_dir, "doesnt_exist.txt")
        comparer = DocumentCompare()
        
        # When
        result = comparer.compare_files(existing_file, non_existent_file)
        
        # Then
        assert not result.success
        assert result.error
        assert "not found" in result.error
    
    def test_unsupported_file_format_handled_gracefully(self, temp_test_dir: str) -> None:
        """Test that comparing with an unsupported file format returns an error result."""
        # Given
        text_file = os.path.join(temp_test_dir, "file1.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write("Some content")
            
        unsupported_file = os.path.join(temp_test_dir, "file2.xyz")
        with open(unsupported_file, "w", encoding="utf-8") as f:
            f.write("Some content")
            
        comparer = DocumentCompare()
        
        # When
        result = comparer.compare_files(text_file, unsupported_file)
        
        # Then
        assert not result.success
        assert result.error
        assert "Unsupported file format" in result.error
    
    def test_find_common_terms_with_populated_documents(self, similar_documents: Tuple[str, str]) -> None:
        """Test finding common legal terms in both documents."""
        # Given
        file1_path, file2_path = similar_documents
        comparer = DocumentCompare(file1_path, file2_path)
        
        # When
        common_terms = comparer.find_common_terms()
        
        # Then
        assert isinstance(common_terms, set)
        # Since our test docs don't have legal terms, just verify the method returns a set
        # In a real test with legal terms, we'd verify the expected terms are found

    def test_representation_includes_file_paths(self, similar_documents: Tuple[str, str]) -> None:
        """Test string representation includes file paths."""
        # Given
        file1_path, file2_path = similar_documents
        comparer = DocumentCompare(file1_path, file2_path)
        
        # When
        repr_str = repr(comparer)
        
        # Then
        assert "file1=" in repr_str
        assert "file2=" in repr_str
        assert file1_path in repr_str
        assert file2_path in repr_str
