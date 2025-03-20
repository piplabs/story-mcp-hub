#!/usr/bin/env python
"""
Test Runner for Story MCP Hub

This script provides a convenient way to run tests for the Story MCP Hub project with
proper environment setup. It handles:

1. Setting up the Python path to include all relevant project directories
2. Loading environment variables from .env.test
3. Running pytest with appropriate options
4. Generating coverage reports

Usage:
  python run_tests.py                     # Run all tests
  python run_tests.py -t tests/unit/      # Run all unit tests
  python run_tests.py -v                  # Run with verbose output
  python run_tests.py --no-cov            # Run without coverage reporting
  python run_tests.py --help              # Show help message

For more information, see TESTING.md
"""
import pytest
import os
import sys
from pathlib import Path
import argparse
from dotenv import load_dotenv


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run tests with environment setup")
    parser.add_argument(
        "-t", "--test",
        help="Specific test file or directory to run (e.g., 'tests/unit/story_sdk_mcp')",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Verbose output",
        action="store_true"
    )
    parser.add_argument(
        "--no-cov",
        help="Disable coverage reporting",
        action="store_true"
    )
    args = parser.parse_args()

    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.append(str(project_root))
    sys.path.append(str(project_root / "story-sdk-mcp"))
    sys.path.append(str(project_root / "storyscan-mcp"))
    sys.path.append(str(project_root / "tests"))

    # Load environment variables from .env.test
    env_file = os.path.join(project_root, '.env.test')
    load_dotenv(env_file)

    # Output the loaded environment variables without showing full private key
    private_key = os.environ.get("WALLET_PRIVATE_KEY", "")
    if private_key:
        print(f"WALLET_PRIVATE_KEY loaded (starts with): {private_key[:6]}...")
    else:
        print("WARNING: WALLET_PRIVATE_KEY not loaded!")

    # Prepare pytest arguments
    pytest_args = []

    # Add test path if specified
    if args.test:
        pytest_args.append(args.test)
    else:
        # If no test specified, run all tests
        pytest_args.append("tests")

    # Add verbosity flag
    if args.verbose:
        pytest_args.append("-v")

    # Add coverage reporting unless disabled
    if not args.no_cov:
        pytest_args.extend(["--cov=.", "--cov-report=term-missing"])

    # Run the tests
    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
