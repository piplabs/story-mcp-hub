#!/usr/bin/env python3
"""
Test script for the specialized agent system.
This bypasses the relative import issues for testing purposes.
"""

import sys
import os
import asyncio

# Add the story-sdk-mcp directory to Python path
story_sdk_mcp_path = os.path.join(os.path.dirname(__file__), "story-sdk-mcp")
sys.path.insert(0, story_sdk_mcp_path)

# Import directly from the specialized-agent package (note the hyphen)
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(story_sdk_mcp_path, "specialized-agent", "main.py"))
main_module = importlib.util.module_from_spec(spec)
sys.modules["main"] = main_module
spec.loader.exec_module(main_module)

run_conversation = main_module.run_conversation

if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)