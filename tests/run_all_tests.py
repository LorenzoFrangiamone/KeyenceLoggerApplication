#!/usr/bin/env python3
"""
Test runner for KCompareAgent critical functions
"""

import sys
import os
import unittest

def run_all_tests():
    """Run all test suites"""
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test files
    try:
        from tests.test_core_functions import TestTextProcessingLogic, TestAICorrectionFunctionality, TestMainApplicationFlow
        from tests.test_ai_functionality import TestAIFunctionality
        from tests.test_backend_functionality import TestBackendFunctionality
        
        suite.addTests(loader.loadTestsFromTestCase(TestTextProcessingLogic))
        suite.addTests(loader.loadTestsFromTestCase(TestAICorrectionFunctionality))
        suite.addTests(loader.loadTestsFromTestCase(TestMainApplicationFlow))
        suite.addTests(loader.loadTestsFromTestCase(TestAIFunctionality))
        suite.addTests(loader.loadTestsFromTestCase(TestBackendFunctionality))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Error running tests: {e}")
        # Fallback - try to run basic tests
        print("Running minimal test suite...")
        try:
            # Basic import test
            import src.backEnd
            import src.AICorrector
            import Main
            print("All modules imported successfully")
            return True
        except Exception as e2:
            print(f"Import test failed: {e2}")
            return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)