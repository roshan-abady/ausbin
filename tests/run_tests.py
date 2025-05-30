# run_tests.py
import unittest
import sys
import os
import subprocess
import importlib.util

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def is_venv_active():
    """Check if running inside a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['pytest']
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            print(f"❌ Required package '{package}' is not installed")
            return False
    return True

if __name__ == '__main__':
    # Check if running in virtual environment
    if not is_venv_active():
        print("⚠️  Not running in virtual environment. For best results, activate it first:")
        print("    source venv/bin/activate")
        print("    # OR run")
        print("    source activate.sh")
        
        # Attempt to continue with system Python
        print("\n🔄 Attempting to run tests with system Python...")
        
        # Check dependencies
        if not check_dependencies():
            print("❌ Please activate the virtual environment or install required packages:")
            print("   python -m pip install -r requirements.txt")
            sys.exit(1)
    
    print("🚀 Running tests...\n")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
