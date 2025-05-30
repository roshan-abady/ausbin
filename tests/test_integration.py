# tests/test_integration.py
import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.business_names_api import BusinessNamesAPI, BusinessNamesAPIError

"""
Integration tests for the Business Names API.

Author: Roshan Abady
Email: roshanabady@gmail.com
"""

class TestIntegration(unittest.TestCase):
    """Integration tests for live API connectivity"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with API instance"""
        cls.api = BusinessNamesAPI()
    
    def test_api_connectivity(self):
        """Test basic API connectivity"""
        result = self.api.test_connection()
        self.assertTrue(result, "API connection should be successful")
    
    def test_basic_search(self):
        """Test basic search functionality"""
        result = self.api.search_business_names(limit=5)
        
        self.assertTrue(result.get('success'), "Search should return success=True")
        
        records = result.get('result', {}).get('records', [])
        self.assertGreater(len(records), 0, "Should return at least one record")
        self.assertLessEqual(len(records), 5, "Should respect limit parameter")
    
    def test_query_search(self):
        """Test query-based search"""
        result = self.api.search_business_names(query="PTY", limit=3)
        
        self.assertTrue(result.get('success'), "Query search should be successful")
        
        records = result.get('result', {}).get('records', [])
        self.assertLessEqual(len(records), 3, "Should respect limit parameter")
    
    def test_sql_search(self):
        """Test SQL search functionality"""
        sql_query = f'''
        SELECT "BN_NAME", "BN_STATUS" 
        FROM "{self.api.config.resource_id}" 
        WHERE "BN_STATUS" = 'Registered'
        LIMIT 3
        '''
        
        result = self.api.search_business_names_sql(sql_query)
        
        self.assertTrue(result.get('success'), "SQL search should be successful")
        
        records = result.get('result', {}).get('records', [])
        self.assertLessEqual(len(records), 3, "Should respect LIMIT clause")
        
        # Verify all returned records have 'Registered' status
        for record in records:
            self.assertEqual(
                record.get('BN_STATUS'), 
                'Registered', 
                "All records should have 'Registered' status"
            )
    
    def test_error_handling(self):
        """Test error handling with invalid requests"""
        with self.assertRaises(BusinessNamesAPIError):
            self.api.search_business_names_sql("INVALID SQL QUERY")
    
    def test_performance(self):
        """Test basic performance metrics"""
        import time
        
        start_time = time.time()
        result = self.api.search_business_names(limit=100)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertTrue(result.get('success'), "Performance test should succeed")
        self.assertLess(response_time, 30, "Response should complete within 30 seconds")
        
        records = result.get('result', {}).get('records', [])
        self.assertLessEqual(len(records), 100, "Should respect limit parameter")

if __name__ == '__main__':
    unittest.main(verbosity=2)
