from typing import Literal
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import ToolMessage

from .state import State
from .primary_assistant import primary_assistant, primary_assistant_tools, route_primary_assistant

# Import all specialist entry nodes and routing functions
from .specialists.dispute import (
    enter_dispute, create_dispute_assistant, route_dispute,
    get_dispute_safe_tool_node, get_dispute_sensitive_tool_node
)
from .specialists.ipaccount import (
    enter_ipaccount, create_ipaccount_assistant, route_ipaccount,
    get_ipaccount_safe_tool_node, get_ipaccount_sensitive_tool_node
)
from .specialists.ipasset import (
    enter_ipasset, create_ipasset_assistant, route_ipasset,
    get_ipasset_safe_tool_node, get_ipasset_sensitive_tool_node
)
from .specialists.license import (
    enter_license, create_license_assistant, route_license,
    get_license_safe_tool_node, get_license_sensitive_tool_node
)
from .specialists.nftclient import (
    enter_nftclient, create_nftclient_assistant, route_nftclient,
    get_nftclient_safe_tool_node, get_nftclient_sensitive_tool_node
)
from .specialists.royalty import (
    enter_royalty, create_royalty_assistant, route_royalty,
    get_royalty_safe_tool_node, get_royalty_sensitive_tool_node
)
from .specialists.wip import (
    enter_wip, create_wip_assistant, route_wip,
    get_wip_safe_tool_node, get_wip_sensitive_tool_node
)

from .mcp_integration import initialize_mcp_integration


def user_info(state: State):
    """Pre-populate user info to avoid unnecessary tool calls."""
    return {"user_info": f"User wallet address: {state.get('wallet_address', 'Not provided')}"}


def route_to_workflow(state: State) -> Literal[
    "primary_assistant",
    "dispute",
    "ipaccount", 
    "ipasset",
    "license",
    "nftclient",
    "royalty",
    "wip"
]:
    """If we are in a delegated state, route directly to the appropriate assistant."""
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]


# Shared node for exiting specialized assistants
def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.
    
    This lets the full graph explicitly track the dialog flow and delegate
    control to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs
        # parallel tool calls
        messages.append(
            ToolMessage(
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
                content="Resuming dialog with the host assistant. Please reflect "
                "on the past conversation and assist the user as needed.",
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }


async def create_specialized_agent_graph():
    """Create the specialized agent graph with MCP tool integration"""
    # Initialize MCP integration first
    await initialize_mcp_integration()
    
    # Create all specialist assistants with MCP tools
    dispute_assistant = create_dispute_assistant()
    ipaccount_assistant = create_ipaccount_assistant()
    ipasset_assistant = create_ipasset_assistant()
    license_assistant = create_license_assistant()
    nftclient_assistant = create_nftclient_assistant()
    royalty_assistant = create_royalty_assistant()
    wip_assistant = create_wip_assistant()
    
    # Create the graph
    builder = StateGraph(State)

    # Add entry node
    builder.add_node("fetch_user_info", user_info)
    builder.set_entry_point("fetch_user_info")

    # Primary assistant
    builder.add_node("primary_assistant", primary_assistant)
    builder.add_node(
        "primary_assistant_tools",
        ToolNode(primary_assistant_tools),
    )

    # Dispute assistant workflow
    builder.add_node("enter_dispute", enter_dispute)
    builder.add_node("dispute", dispute_assistant)
    builder.add_node("dispute_safe_tools", get_dispute_safe_tool_node())
    builder.add_node("dispute_sensitive_tools", get_dispute_sensitive_tool_node())

    # IPAccount assistant workflow  
    builder.add_node("enter_ipaccount", enter_ipaccount)
    builder.add_node("ipaccount", ipaccount_assistant)
    builder.add_node("ipaccount_safe_tools", get_ipaccount_safe_tool_node())
    builder.add_node("ipaccount_sensitive_tools", get_ipaccount_sensitive_tool_node())

    # IPAsset assistant workflow
    builder.add_node("enter_ipasset", enter_ipasset)  
    builder.add_node("ipasset", ipasset_assistant)
    builder.add_node("ipasset_safe_tools", get_ipasset_safe_tool_node())
    builder.add_node("ipasset_sensitive_tools", get_ipasset_sensitive_tool_node())

    # License assistant workflow
    builder.add_node("enter_license", enter_license)
    builder.add_node("license", license_assistant)
    builder.add_node("license_safe_tools", get_license_safe_tool_node())
    builder.add_node("license_sensitive_tools", get_license_sensitive_tool_node())

    # NFTClient assistant workflow
    builder.add_node("enter_nftclient", enter_nftclient)
    builder.add_node("nftclient", nftclient_assistant)
    builder.add_node("nftclient_safe_tools", get_nftclient_safe_tool_node())
    builder.add_node("nftclient_sensitive_tools", get_nftclient_sensitive_tool_node())

    # Royalty assistant workflow
    builder.add_node("enter_royalty", enter_royalty)
    builder.add_node("royalty", royalty_assistant)
    builder.add_node("royalty_safe_tools", get_royalty_safe_tool_node())
    builder.add_node("royalty_sensitive_tools", get_royalty_sensitive_tool_node())

    # WIP assistant workflow
    builder.add_node("enter_wip", enter_wip)
    builder.add_node("wip", wip_assistant)  
    builder.add_node("wip_safe_tools", get_wip_safe_tool_node())
    builder.add_node("wip_sensitive_tools", get_wip_sensitive_tool_node())

    # Shared exit node
    builder.add_node("leave_skill", pop_dialog_state)

    # Primary assistant routing
    builder.add_conditional_edges("fetch_user_info", route_to_workflow)
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        {
            "enter_dispute": "enter_dispute",
            "enter_ipaccount": "enter_ipaccount", 
            "enter_ipasset": "enter_ipasset",
            "enter_license": "enter_license",
            "enter_nftclient": "enter_nftclient",
            "enter_royalty": "enter_royalty",
            "enter_wip": "enter_wip",
            "primary_assistant_tools": "primary_assistant_tools",
            "END": "__end__"
        },
    )
    builder.add_edge("primary_assistant_tools", "primary_assistant")

    # Dispute workflow edges
    builder.add_edge("enter_dispute", "dispute")
    builder.add_conditional_edges(
        "dispute",
        route_dispute,
        {
            "dispute_safe_tools": "dispute_safe_tools",
            "dispute_sensitive_tools": "dispute_sensitive_tools", 
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )
    builder.add_edge("dispute_safe_tools", "dispute")
    builder.add_edge("dispute_sensitive_tools", "dispute")

    # IPAccount workflow edges
    builder.add_edge("enter_ipaccount", "ipaccount")
    builder.add_conditional_edges(
        "ipaccount",
        route_ipaccount,
        {
            "ipaccount_safe_tools": "ipaccount_safe_tools",
            "ipaccount_sensitive_tools": "ipaccount_sensitive_tools",
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )
    builder.add_edge("ipaccount_safe_tools", "ipaccount")
    builder.add_edge("ipaccount_sensitive_tools", "ipaccount")

    # IPAsset workflow edges
    builder.add_edge("enter_ipasset", "ipasset")
    builder.add_conditional_edges(
        "ipasset",
        route_ipasset,
        {
            "ipasset_safe_tools": "ipasset_safe_tools",
            "ipasset_sensitive_tools": "ipasset_sensitive_tools",
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )
    builder.add_edge("ipasset_safe_tools", "ipasset")
    builder.add_edge("ipasset_sensitive_tools", "ipasset")

    # License workflow edges
    builder.add_edge("enter_license", "license")
    builder.add_conditional_edges(
        "license",
        route_license,
        {
            "license_safe_tools": "license_safe_tools",
            "license_sensitive_tools": "license_sensitive_tools",
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )
    builder.add_edge("license_safe_tools", "license")
    builder.add_edge("license_sensitive_tools", "license")

    # NFTClient workflow edges
    builder.add_edge("enter_nftclient", "nftclient")
    builder.add_conditional_edges(
        "nftclient", 
        route_nftclient,
        {
            "nftclient_safe_tools": "nftclient_safe_tools",
            "nftclient_sensitive_tools": "nftclient_sensitive_tools",
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )
    builder.add_edge("nftclient_safe_tools", "nftclient")
    builder.add_edge("nftclient_sensitive_tools", "nftclient")

    # Royalty workflow edges
    builder.add_edge("enter_royalty", "royalty")
    builder.add_conditional_edges(
        "royalty",
        route_royalty,
        {
            "royalty_safe_tools": "royalty_safe_tools",
            "royalty_sensitive_tools": "royalty_sensitive_tools",
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )  
    builder.add_edge("royalty_safe_tools", "royalty")
    builder.add_edge("royalty_sensitive_tools", "royalty")

    # WIP workflow edges
    builder.add_edge("enter_wip", "wip")
    builder.add_conditional_edges(
        "wip",
        route_wip,
        {
            "wip_safe_tools": "wip_safe_tools",
            "wip_sensitive_tools": "wip_sensitive_tools",
            "leave_skill": "leave_skill",
            "END": "__end__"
        },
    )
    builder.add_edge("wip_safe_tools", "wip")
    builder.add_edge("wip_sensitive_tools", "wip")

    # Shared exit edge
    builder.add_edge("leave_skill", "primary_assistant")

    # Compile graph with interrupt_before for sensitive tools
    memory = InMemorySaver()
    graph = builder.compile(
        checkpointer=memory,
        # Let the user approve or deny the use of sensitive tools
        interrupt_before=[
            "dispute_sensitive_tools",
            "ipaccount_sensitive_tools",
            "ipasset_sensitive_tools", 
            "license_sensitive_tools",
            "nftclient_sensitive_tools",
            "royalty_sensitive_tools",
            "wip_sensitive_tools",
        ],
    )
    
    return graph


# Global graph instance (created async)
_graph = None


async def get_specialized_agent_graph():
    """Get the initialized specialized agent graph"""
    global _graph
    
    if _graph is None:
        _graph = await create_specialized_agent_graph()
    
    return _graph