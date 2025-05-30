# Author: Roshan Abady
# business_names_api.py
# AUSBIN - Australian Business Names Register API

import requests
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin
import json
import time

# Configure logging at module level - BEFORE any usage
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration class for API settings"""
    base_url: str = "https://data.gov.au/data/api/action/"
    resource_id: str = "55ad4b1c-5eeb-44ea-8b29-d410da431be3"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    default_limit: int = 100

class BusinessNamesAPIError(Exception):
    """Custom exception for API-related errors"""
    pass

class BusinessNamesAPI:
    """
    Production-ready client for accessing AUSBIN - Australian Business Names Register API
    
    Implements robust error handling, retry mechanisms, and rate limiting
    for enterprise-grade data pipeline integration.
    
    Author: Roshan Abady
    Email: roshanabady@gmail.com
    """
    
    def __init__(self, config: Optional[APIConfig] = None, api_token: Optional[str] = None):
        """
        Initialize the API client
        
        Args:
            config: API configuration object
            api_token: Optional API token for authenticated requests
        """
        self.config = config or APIConfig()
        self.api_token = api_token
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create configured requests session with proper headers"""
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BusinessNamesAPI/1.0'
        })
        
        if self.api_token:
            session.headers['Authorization'] = self.api_token
            
        return session
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Make API request with retry logic and error handling
        
        Args:
            endpoint: API endpoint (e.g., 'datastore_search')
            params: Request parameters
            
        Returns:
            API response data
            
        Raises:
            BusinessNamesAPIError: For API-related errors
        """
        url = urljoin(self.config.base_url, endpoint)
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Making API request to {endpoint} (attempt {attempt + 1})")
                
                response = self.session.post(
                    url,
                    json=params,
                    timeout=self.config.timeout
                )
                
                # Handle HTTP errors
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Check for CKAN API errors
                if not data.get('success', False):
                    error_msg = data.get('error', {})
                    raise BusinessNamesAPIError(f"API error: {error_msg}")
                
                logger.info(f"Successfully retrieved {len(data.get('result', {}).get('records', []))} records")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                
                if attempt == self.config.max_retries - 1:
                    raise BusinessNamesAPIError(f"Failed to connect after {self.config.max_retries} attempts: {e}")
                
                # Exponential backoff
                time.sleep(self.config.retry_delay * (2 ** attempt))
                
            except json.JSONDecodeError as e:
                raise BusinessNamesAPIError(f"Invalid JSON response: {e}")
    
    def search_business_names(
        self, 
        query: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Dict:
        """
        Search business names using the datastore_search endpoint
        
        Args:
            query: Free text search query
            filters: Dictionary of field filters
            limit: Maximum number of records to return (None for all available)
            offset: Number of records to skip
            
        Returns:
            API response containing business names data
        """
        params = {
            'resource_id': self.config.resource_id,
            'offset': offset
        }
        
        # Set limit - use large number if None to get all records
        if limit is None:
            params['limit'] = 100000  # Large number to get all available records
        else:
            params['limit'] = limit
        
        if query:
            params['q'] = query
            
        if filters:
            params['filters'] = filters
            
        return self._make_request('datastore_search', params)
    
    def search_business_names_sql(self, sql_query: str) -> Dict:
        """
        Execute SQL query against the business names dataset
        
        Args:
            sql_query: SQL query string
            
        Returns:
            API response containing query results
        """
        params = {'sql': sql_query}
        return self._make_request('datastore_search_sql', params)
    
    def get_resource_info(self) -> Dict:
        """
        Get metadata about the business names resource
        
        Returns:
            Resource metadata
        """
        params = {'id': self.config.resource_id}
        return self._make_request('resource_show', params)
    
    def test_connection(self) -> bool:
        """
        Test API connectivity with a minimal request
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = self.search_business_names(limit=1)
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Example usage and testing script
if __name__ == "__main__":
    # Initialize API client
    api = BusinessNamesAPI()
    
    # Test connection
    print("Testing API connection...")
    if api.test_connection():
        print("✓ Connection successful!")
        
        # Fetch sample data
        print("\nFetching sample business names...")
        result = api.search_business_names(limit=5)
        
        records = result.get('result', {}).get('records', [])
        for i, record in enumerate(records, 1):
            name = record.get('BN_NAME', 'N/A')
            status = record.get('BN_STATUS', 'N/A')
            print(f"{i}. {name} (Status: {status})")
            
    else:
        print("✗ Connection failed!")
