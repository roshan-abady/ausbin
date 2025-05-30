# tests/test_business_names_api.py
import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock, patch, MagicMock
import requests
import json
from src.business_names_api import BusinessNamesAPI, APIConfig, BusinessNamesAPIError

class TestBusinessNamesAPI(unittest.TestCase):
    """Comprehensive test suite for BusinessNamesAPI"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = APIConfig()
        self.api = BusinessNamesAPI(self.config)
        
        # Mock response data
        self.mock_success_response = {
            'success': True,
            'result': {
                'records': [
                    {
                        'BN_NAME': 'TEST BUSINESS PTY LTD',
                        'BN_STATUS': 'Registered',
                        'BN_REG_DT': '2023-01-01'
                    }
                ],
                'total': 1
            }
        }
        
        self.mock_error_response = {
            'success': False,
            'error': {
                'message': 'Resource not found'
            }
        }
    
    def test_api_initialization(self):
        """Test API client initialization"""
        # Test default initialization
        api = BusinessNamesAPI()
        self.assertIsInstance(api.config, APIConfig)
        self.assertIsNone(api.api_token)
        
        # Test with custom config and token
        config = APIConfig(timeout=60)
        api_with_token = BusinessNamesAPI(config, "test_token")
        self.assertEqual(api_with_token.config.timeout, 60)
        self.assertEqual(api_with_token.api_token, "test_token")
        self.assertEqual(api_with_token.session.headers['Authorization'], "test_token")
    
    @patch('src.business_names_api.requests.Session.post')
    def test_successful_search(self, mock_post):
        """Test successful business name search"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_success_response
        mock_post.return_value = mock_response
        
        # Execute search
        result = self.api.search_business_names(query="test", limit=10)
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        self.assertIn('json', call_args.kwargs)
        request_data = call_args.kwargs['json']
        self.assertEqual(request_data['resource_id'], self.config.resource_id)
        self.assertEqual(request_data['q'], "test")
        self.assertEqual(request_data['limit'], 10)
        
        # Verify response
        self.assertEqual(result, self.mock_success_response)
    
    @patch('src.business_names_api.requests.Session.post')
    def test_search_with_filters(self, mock_post):
        """Test search with filters"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_success_response
        mock_post.return_value = mock_response
        
        filters = {'BN_STATUS': 'Registered'}
        result = self.api.search_business_names(filters=filters)
        
        call_args = mock_post.call_args
        request_data = call_args.kwargs['json']
        self.assertEqual(request_data['filters'], filters)
    
    @patch('src.business_names_api.requests.Session.post')
    def test_sql_search(self, mock_post):
        """Test SQL query functionality"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_success_response
        mock_post.return_value = mock_response
        
        sql_query = 'SELECT * FROM "55ad4b1c-5eeb-44ea-8b29-d410da431be3" LIMIT 5'
        result = self.api.search_business_names_sql(sql_query)
        
        call_args = mock_post.call_args
        request_data = call_args.kwargs['json']
        self.assertEqual(request_data['sql'], sql_query)
    
    @patch('src.business_names_api.requests.Session.post')
    def test_api_error_handling(self, mock_post):
        """Test API error response handling"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_error_response
        mock_post.return_value = mock_response
        
        with self.assertRaises(BusinessNamesAPIError) as context:
            self.api.search_business_names()
        
        self.assertIn("API error", str(context.exception))
    
    @patch('src.business_names_api.requests.Session.post')
    def test_http_error_handling(self, mock_post):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        with self.assertRaises(BusinessNamesAPIError):
            self.api.search_business_names()
    
    @patch('src.business_names_api.requests.Session.post')
    def test_retry_mechanism(self, mock_post):
        """Test retry mechanism on connection failure"""
        # Mock connection error for first two attempts, success on third
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.ConnectionError("Connection failed"),
            Mock(raise_for_status=Mock(), json=Mock(return_value=self.mock_success_response))
        ]
        
        # Should succeed after retries
        result = self.api.search_business_names()
        self.assertEqual(mock_post.call_count, 3)
    
    @patch('src.business_names_api.requests.Session.post')
    def test_max_retries_exceeded(self, mock_post):
        """Test behavior when max retries exceeded"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with self.assertRaises(BusinessNamesAPIError) as context:
            self.api.search_business_names()
        
        self.assertEqual(mock_post.call_count, self.config.max_retries)
        self.assertIn("Failed to connect after", str(context.exception))
    
    @patch('src.business_names_api.requests.Session.post')
    def test_json_decode_error(self, mock_post):
        """Test handling of invalid JSON response"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response
        
        with self.assertRaises(BusinessNamesAPIError) as context:
            self.api.search_business_names()
        
        self.assertIn("Invalid JSON response", str(context.exception))
    
    @patch('src.business_names_api.requests.Session.post')
    def test_connection_test(self, mock_post):
        """Test connection testing functionality"""
        # Test successful connection
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.mock_success_response
        mock_post.return_value = mock_response
        
        self.assertTrue(self.api.test_connection())
        
        # Test failed connection
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        self.assertFalse(self.api.test_connection())
    
    def test_config_validation(self):
        """Test configuration parameter validation"""
        config = APIConfig(
            base_url="https://custom.api.url/",
            resource_id="custom-resource-id",
            timeout=60,
            max_retries=5
        )
        
        api = BusinessNamesAPI(config)
        self.assertEqual(api.config.base_url, "https://custom.api.url/")
        self.assertEqual(api.config.resource_id, "custom-resource-id")
        self.assertEqual(api.config.timeout, 60)
        self.assertEqual(api.config.max_retries, 5)

class TestAPIConfig(unittest.TestCase):
    """Test APIConfig dataclass"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = APIConfig()
        self.assertEqual(config.base_url, "https://data.gov.au/data/api/action/")
        self.assertEqual(config.resource_id, "55ad4b1c-5eeb-44ea-8b29-d410da431be3")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.default_limit, 100)

if __name__ == '__main__':
    unittest.main(verbosity=2)
