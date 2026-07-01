# KCompareAgent Test Suite

This directory contains automated tests for the three most critical functions of KCompareAgent.

## Test Files Overview

1. **test_core_functions.py** - Tests for core functionality including:
   - Text processing and comparison logic
   - AI correction functionality  
   - Main application flow

2. **test_ai_functionality.py** - Specific tests for AI correction features

3. **test_backend_functionality.py** - Tests for backend text processing capabilities

4. **run_all_tests.py** - Test runner script to execute all tests

## How to Run Tests

### Method 1: Using the test runner
```bash
python tests/run_all_tests.py
```

### Method 2: Using pytest
```bash
cd tests
pytest -v
```

### Method 3: Running individual test files
```bash
python -m unittest tests/test_core_functions.py -v
python -m unittest tests/test_ai_functionality.py -v
python -m unittest tests/test_backend_functionality.py -v
```

## Test Coverage

The tests cover:
- **Text Processing Logic**: Empty strings, simple comparisons, special characters
- **AI Correction**: Initialization, method existence, basic functionality
- **Main Flow**: Application startup, GUI initialization
- **Error Handling**: Graceful failure scenarios
- **Integration**: End-to-end workflow testing

## Requirements

The tests require:
- Python 3.6+
- unittest (standard library)
- mock (for testing)
- pytest (optional, for enhanced testing)

Install test dependencies with:
```bash
pip install -r tests/requirements_test.txt
```