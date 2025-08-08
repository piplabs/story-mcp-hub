#!/usr/bin/env python3
"""
Run the Story Protocol Specialized Agent in terminal.
This script properly handles the module imports.
"""

import sys
import os
import asyncio
import uuid
from typing import Dict, Any

# Fix Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
story_sdk_path = os.path.join(current_dir, "story-sdk-mcp")
sys.path.insert(0, story_sdk_path)

# Import as a package with proper namespace
from specialized_agent.graph import get_specialized_agent_graph
from specialized_agent.state import State
from langchain_core.messages import ToolMessage


def print_event(event: Dict[str, Any], _printed: set):
    """Pretty print graph events for debugging."""
    current_node = list(event.keys())[0]
    if current_node in _printed:
        return
    _printed.add(current_node)
    
    print(f"\n--- Node: {current_node} ---")
    
    if 'messages' in event[current_node]:
        messages = event[current_node]['messages']
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content') and last_message.content:
                print(f"Content: {last_message.content[:200]}...")
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                print(f"Tool calls: {[tc['name'] for tc in last_message.tool_calls]}")


async def run_conversation():
    """Run the specialized agent conversation in terminal."""
    print("=== Story Protocol Specialized Agent System ===")
    print("Following LangGraph tutorial patterns with interrupt_before confirmation")
    print("\nWallet Address: 0xeC2E8ae2F6c9BE6C876629198Cc554c17e9Ff2C4")
    print("\nAvailable specialists:")
    print("  • Dispute: raise_dispute")
    print("  • IPAccount: get_erc20_token_balance, mint_test_erc20_tokens")
    print("  • IPAsset: mint_and_register_ip_with_terms, register, upload_image_to_ipfs, create_ip_metadata")
    print("  • License: get_license_terms, mint_license_tokens, attach_license_terms")
    print("  • NFTClient: create_spg_nft_collection, get_spg_nft_contract_minting_fee_and_token")
    print("  • Royalty: pay_royalty_on_behalf, claim_all_revenue")
    print("  • WIP: deposit_wip, transfer_wip")
    print("\nType 'quit' to exit.\n")

    # Get the initialized graph with MCP tools
    print("Initializing MCP integration...")
    try:
        graph = await get_specialized_agent_graph()
        print("MCP integration ready!")
    except Exception as e:
        print(f"Error initializing MCP: {e}")
        print("Make sure the Story SDK MCP server is accessible.")
        return

    # Initialize config
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
        }
    }

    # Set initial state
    initial_state = {
        "messages": [],
        "user_info": "",
        "wallet_address": "0xeC2E8ae2F6c9BE6C876629198Cc554c17e9Ff2C4",
        "dialog_state": [],
    }

    _printed = set()

    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue

            # Add user message to state
            events = graph.stream(
                {"messages": ("user", user_input)}, config, stream_mode="values"
            )

            for event in events:
                print_event(event, _printed)
                snapshot = graph.get_state(config)
                
                # Check if we have an interrupt (waiting for user approval)
                if snapshot.next:
                    # We have an interrupt! The agent is trying to use a tool, and the user
                    # can approve or deny it
                    print("\n⚠️  The agent wants to execute a sensitive blockchain operation.")
                    try:
                        user_input = input(
                            "Do you approve? Type 'y' to continue; "
                            "otherwise, explain your requested changes.\n> "
                        )
                    except:
                        user_input = "y"
                    if user_input.strip().lower() == "y":
                        # Just continue
                        result = graph.invoke(
                            None,
                            config,
                        )
                    else:
                        # Satisfy the tool invocation by providing feedback
                        last_message = snapshot.values["messages"][-1]
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            result = graph.invoke(
                                {
                                    "messages": [
                                        ToolMessage(
                                            tool_call_id=last_message.tool_calls[0]["id"],
                                            content=f"API call denied by user. Reasoning: "
                                            f"'{user_input}'. Continue assisting, accounting for the user's input.",
                                        )
                                    ]
                                },
                                config,
                            )
                    snapshot = graph.get_state(config)

            # Print final response
            if snapshot.values.get("messages"):
                last_message = snapshot.values["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    print(f"\nAssistant: {last_message.content}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    # Load .env file for environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set!")
        print("Please set it in your .env file or with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    try:
        asyncio.run(run_conversation())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)