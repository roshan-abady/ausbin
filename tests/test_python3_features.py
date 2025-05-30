# tests/test_python3_features.py
import unittest
from pathlib import Path
import tempfile
import inspect
from unittest.mock import patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Test suite for Python 3 features used in the project.

Author: Roshan Abady
Email: roshanabady@gmail.com
"""

class TestPython3Features(unittest.TestCase):
    """Test Python 3 specific features"""
    
    def test_pathlib_usage(self):
        """Test pathlib Path usage"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            cache_dir.mkdir(exist_ok=True)
            
            self.assertTrue(cache_dir.exists())
            self.assertTrue(cache_dir.is_dir())
    
    def test_f_string_formatting(self):
        """Test f-string usage"""
        name = "Test Business"
        status = "Registered"
        formatted = f"Business: {name} (Status: {status})"
        
        self.assertEqual(formatted, "Business: Test Business (Status: Registered)")
    
    def test_type_hints(self):
        """Test type hints are properly defined"""
        from src.business_names_api import BusinessNamesAPI
        
        # Check that methods have proper type hints
        sig = inspect.signature(BusinessNamesAPI.search_business_names)
        
        # Check parameter type hints
        self.assertIsNotNone(sig.parameters['query'].annotation)
        self.assertIsNotNone(sig.parameters['filters'].annotation)
        self.assertIsNotNone(sig.parameters['limit'].annotation)
        
        # Check return type annotation
        self.assertIsNotNone(sig.return_annotation)
        self.assertNotEqual(sig.return_annotation, inspect.Signature.empty)
    
    def test_dataclass_functionality(self):
        """Test dataclass usage"""
        from src.business_names_api import APIConfig
        
        config = APIConfig(timeout=60, max_retries=5)
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 5)
        self.assertIsInstance(config.base_url, str)
    
    def test_modern_python_features(self):
        """Test various Python 3 features are working"""
        # Test dictionary comprehension
        data = {'a': 1, 'b': 2, 'c': 3}
        squared = {k: v**2 for k, v in data.items()}
        self.assertEqual(squared, {'a': 1, 'b': 4, 'c': 9})
        
        # Test set comprehension
        numbers = [1, 2, 2, 3, 3, 4]
        unique_squares = {x**2 for x in numbers}
        self.assertEqual(unique_squares, {1, 4, 9, 16})
        
        # Test walrus operator (Python 3.8+)
        test_list = [1, 2, 3, 4, 5]
        if (n := len(test_list)) > 3:
            self.assertGreater(n, 3)

if __name__ == '__main__':
    unittest.main(verbosity=2)
