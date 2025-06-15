"""
Verification script to test integration and operation of Lawglance components.
"""
import os
import sys
import logging
import json
import tempfile
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verification")

def verify_configuration():
    """Verify that configuration loading works properly."""
    logger.info("Verifying configuration system...")
    
    from config import Config, DEFAULT_CONFIG
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp_path = temp.name
        # Add a custom setting to verify loading
        test_config = DEFAULT_CONFIG.copy()
        test_config["test_section"] = {"test_key": "test_value"}
        json.dump(test_config, temp)
    
    try:
        # Test loading the config
        config = Config(temp_path)
        test_value = config.get("test_section", "test_key")
        
        # Verify values
        assert test_value == "test_value", "Failed to load custom config value"
        assert config.get("models", "llm") == DEFAULT_CONFIG["models"]["llm"], "Default values not preserved"
        
        # Test setting and saving values
        config.set("test_section", "new_key", "new_value")
        config.save()
        
        # Reload and verify
        config2 = Config(temp_path)
        assert config2.get("test_section", "new_key") == "new_value", "Failed to save and reload config"
        
        logger.info("✓ Configuration system verification passed")
        return True
    except Exception as e:
        logger.error(f"× Configuration verification failed: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

def verify_document_cache():
    """Verify that document caching works properly."""
    logger.info("Verifying document cache system...")
    
    from config import Config
    from document_cache import DocumentCache
    
    config = Config()
    config.set("caching", "enabled", True)
    config.set("caching", "cache_dir", tempfile.mkdtemp())
    
    cache = DocumentCache(config)
    
    try:
        # Test in-memory cache
        cache.cache_document_content("test_path", "test content")
        content = cache.get_document_content("test_path")
        assert content == "test content", "In-memory cache retrieval failed"
        
        # Test disk cache persistence
        cache2 = DocumentCache(config)
        content2 = cache2.get_document_content("test_path")
        assert content2 == "test content", "Disk cache persistence failed"
        
        # Test analysis cache
        analysis = {"summary": "test", "key_points": ["point1"]}
        cache.cache_document_analysis("test_path", analysis)
        cached_analysis = cache.get_document_analysis("test_path")
        assert cached_analysis["summary"] == "test", "Analysis cache retrieval failed"
        
        # Test invalidation
        cache.invalidate("test_path")
        assert cache.get_document_content("test_path") is None, "Cache invalidation failed"
        
        logger.info("✓ Document cache verification passed")
        return True
    except Exception as e:
        logger.error(f"× Document cache verification failed: {str(e)}")
        return False
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(config.get("caching", "cache_dir"))
        except:
            pass

def verify_document_processor():
    """Verify that document processor works properly."""
    logger.info("Verifying document processor...")
    
    from config import Config
    from document_cache import DocumentCache
    from document_processor import DocumentProcessor
    
    config = Config()
    
    # Create mock components
    word_processor = type('MockWordProcessor', (), {'read_document': lambda self, path: "This is a test document."})()
    doc_analyzer = type('MockDocAnalyzer', (), {'analyze': lambda self, text: {
        "summary": "Test summary", 
        "key_points": ["point1"], 
        "complexity_score": 50, 
        "document_type": "test"
    }})()
    concept_extractor = type('MockConceptExtractor', (), {'extract_concepts': lambda self, text: {
        "test_concept": ["reference"]
    }})()
    
    cache = DocumentCache(config)
    processor = DocumentProcessor(config, word_processor, doc_analyzer, concept_extractor, cache)
    
    try:
        # Create a test document
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp_path = temp.name
            temp.write(b"Test document content")
        
        # Test document processing
        result = processor.process_document(temp_path, analyze=True)
        
        assert "content" in result, "Document content not returned"
        assert "summary" in result, "Document analysis not returned"
        assert "concepts" in result, "Document concepts not returned"
        
        # Test document chunking
        text = "This is the first sentence. This is the second sentence. " * 50
        chunks = processor.chunk_document(text, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 1, "Document not properly chunked"
        
        # Test overlap between chunks
        chunk1_text = chunks[0]["text"]
        chunk2_text = chunks[1]["text"]
        
        assert any(sent in chunk2_text for sent in chunk1_text.split(".")), "No overlap between chunks"
        
        logger.info("✓ Document processor verification passed")
        return True
    except Exception as e:
        logger.error(f"× Document processor verification failed: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

def verify_integration_setup():
    """Verify that Lawglance integration works properly."""
    logger.info("Verifying Lawglance integration...")
    
    # Mock Lawglance class for testing
    class MockLawglance:
        def __init__(self):
            self.word_processor = type('MockWordProcessor', (), {'read_document': lambda self, path: "Test content"})()
            self.doc_analyzer = type('MockDocAnalyzer', (), {'analyze': lambda self, text: {"summary": "Test"}})()
            self.concept_extractor = type('MockConceptExtractor', (), {'extract_concepts': lambda self, text: {}})()
            self.qa_pipeline = lambda question, context: {"answer": "Test answer", "score": 0.9}
        
        def process_document(self, file_path, analyze=False):
            return {"content": "Original content"}
            
        def generate_answer(self, context, question):
            return "Original answer"
    
    try:
        from lawglance_integration import LawglanceIntegration
        
        # Set up integration
        integration = LawglanceIntegration()
        
        # Create mock Lawglance instance
        lawglance = MockLawglance()
        
        # Apply enhancements
        enhanced = integration.setup_lawglance(lawglance)
        
        # Verify original methods are preserved
        assert hasattr(enhanced, '_original_process_document'), "Original method not preserved"
        assert enhanced._original_process_document != enhanced.process_document, "Method not enhanced"
        
        # Create test file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp_path = temp.name
            temp.write(b"Test content for integration")
        
        # Test enhanced document processing
        try:
            result = enhanced.process_document(temp_path)
            assert isinstance(result, dict), "Process document not returning expected result type"
        except Exception as e:
            logger.error(f"Enhanced process_document failed: {e}")
            return False
            
        # Test enhanced answer generation
        try:
            result = enhanced.generate_answer("Test context", "Test question")
            assert isinstance(result, str), "Generate answer not returning expected result type"
        except Exception as e:
            logger.error(f"Enhanced generate_answer failed: {e}")
            return False
        
        logger.info("✓ Lawglance integration verification passed")
        return True
    except Exception as e:
        logger.error(f"× Lawglance integration verification failed: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

def verify_api_token():
    """Verify that the Hugging Face API token is configured and works."""
    logger.info("Verifying API token...")
    
    # Skip actual API call if token not set
    token = os.environ.get("HUGGINGFACE_API_TOKEN")
    if not token:
        from config import Config
        config = Config()
        token = config.get("api_keys", "huggingface_token")
    
    if token == "YOUR_TOKEN_HERE" or not token:
        logger.warning("× No valid API token found - skipping external API verification")
        return None
        
    try:
        import requests
        
        # Test token with a simple API call that doesn't consume much quota
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info("✓ API token verification passed")
            return True
        else:
            logger.error(f"× API token verification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"× API token verification failed: {str(e)}")
        return False

def run_verification():
    """Run all verification tests."""
    print("\nLawglance System Verification")
    print("=" * 60)
    
    results = {}
    
    # Import check
    try:
        import psutil
        module_check = True
    except ImportError:
        logger.warning("psutil module not found - install with: pip install psutil")
        module_check = False
    
    results["imports"] = module_check
    
    # Run all verification tests
    results["config"] = verify_configuration()
    results["cache"] = verify_document_cache()
    results["processor"] = verify_document_processor()
    results["integration"] = verify_integration_setup()
    results["api_token"] = verify_api_token()
    
    # Print summary
    print("\nVerification Results:")
    print("-" * 60)
    for test, result in results.items():
        if result is True:
            status = "✓ PASSED"
        elif result is False:
            status = "× FAILED"
        else:
            status = "- SKIPPED"
        print(f"{test.ljust(15)} {status}")
    print("=" * 60)
    
    # Overall result
    if all(r is True or r is None for r in results.values()):
        print("\nSystem verification completed successfully!")
        return True
    else:
        print("\nSystem verification failed! See logs for details.")
        return False

if __name__ == "__main__":
    run_verification()
