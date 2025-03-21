# Testing Guide for Story MCP Hub

This document provides instructions for running tests in the Story MCP Hub project.

## Prerequisites

- Python 3.12+
- Uv package installer (`pip install uv`)
- Dependencies installed: `uv pip install -e ".[test]"`

## Environment Setup

Tests use environment variables defined in the `.env.test` file. This file is not checked into the git repository for security reasons, but an example file is provided.

To set up your test environment:

1. Copy the example file to create your own `.env.test`:

```bash
cp .env.test.example .env.test
```

2. Edit the `.env.test` file with your test credentials:

```bash
# Open with your preferred editor
nano .env.test
```

Ensure the file contains the necessary variables:

```
# Test environment configuration
TESTING=1

# Story SDK MCP environment variables
WALLET_PRIVATE_KEY=your_private_key_here
RPC_PROVIDER_URL=https://mainnet.storyrpc.io
PINATA_JWT=your_pinata_jwt_here

# StoryScan MCP environment variables
STORYSCAN_API_ENDPOINT=https://www.storyscan.io/api
STORY_API_KEY=your_api_key_here
```

> **Note**: For testing purposes, you can use test accounts with no real assets. The private key provided in the example is only for testing and should not be used in production.

## Running Tests

The project includes a dedicated test runner script (`run_tests.py`) that sets up the Python path and environment variables correctly before running the tests.

### Running All Tests

To run all tests in the project:

```bash
uv run python run_tests.py
```

### Running Specific Tests

To run a specific test file or directory:

```bash
# Run tests in a specific file
uv run python run_tests.py -t tests/unit/story_sdk_mcp/test_story_service.py

# Run all tests in a specific directory
uv run python run_tests.py -t tests/unit/story_sdk_mcp/
```

### Additional Options

The `run_tests.py` script supports several command-line options:

- `-t, --test` - Specify a test file or directory to run
- `-v, --verbose` - Enable verbose output
- `--no-cov` - Disable coverage reporting

Example with multiple options:

```bash
uv run python run_tests.py -t tests/unit/utils/ -v --no-cov
```

### Getting Help

For a complete list of available options:

```bash
uv run python run_tests.py --help
```

## Running Tests with PyTest Directly

If you prefer to use PyTest directly, ensure the environment is properly set up:

```bash
# Use python-dotenv to load environment variables
python -c "from dotenv import load_dotenv; load_dotenv('.env.test'); import pytest; pytest.main(['-v'])"

# Or manually specify the path for pytest to discover tests
PYTHONPATH=. pytest tests/
```

## Test Coverage

By default, running tests with `run_tests.py` generates a coverage report. The coverage output shows:

- Percentage of code covered by tests
- Missing lines that are not covered by tests
- Overall coverage statistics

To view a more detailed HTML coverage report, run:

```bash
uv run python -m pytest --cov=. --cov-report=html
```

This will generate an HTML report in the `htmlcov` directory that you can open in a web browser.
