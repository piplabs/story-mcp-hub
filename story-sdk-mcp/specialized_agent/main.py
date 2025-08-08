#!/usr/bin/env python3
"""
Terminal test runner for Story Protocol Specialized Agent System (Phase 1)

This script demonstrates the LangGraph specialized agent patterns from the tutorial,
adapted for Story Protocol operations with interrupt_before confirmation flow.

Usage:
    python -m specialized-agent.main
"""

import sys
import uuid
import asyncio
from typing import Dict, Any
from langchain_core.messages import ToolMessage

from .graph import get_specialized_agent_graph
from .state import State


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
    print("Phase 1: Terminal Demo")
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
    graph = await get_specialized_agent_graph()
    print("MCP integration ready!")

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
            user_input = input("User: ").strip()
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
                    try:
                        user_input = input(
                            "Do you approve of the above actions? Type 'y' to continue;"
                            " otherwise, explain your requested changed.\n\n"
                        )
                    except:
                        user_input = "y"
                    if user_input.strip() == "y":
                        # Just continue
                        result = graph.invoke(
                            None,
                            config,
                        )
                    else:
                        # Satisfy the tool invocation by
                        # providing instructions on the requested changes / change of mind
                        result = graph.invoke(
                            {
                                "messages": [
                                    ToolMessage(
                                        tool_call_id=event["messages"][-1].tool_calls[0]
                                        ["id"],
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
    try:
        asyncio.run(run_conversation())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)