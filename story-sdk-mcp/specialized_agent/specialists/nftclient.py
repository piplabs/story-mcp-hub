from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# NFT Collection specialist prompt
nftclient_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling NFT Collection operations on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with nft collection operations. "
     "Search for available NFT collections based on the user's preferences and confirm the collection details with the customer. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a nft collection operations operation isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_nftclient_assistant():
    """Create nftclient assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    nftclient_safe_tools = get_specialist_safe_tools("nftclient")
    nftclient_sensitive_tools = get_specialist_sensitive_tools("nftclient")
    
    # Combine with CompleteOrEscalate
    all_nftclient_tools = nftclient_safe_tools + nftclient_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    nftclient_runnable = nftclient_prompt | llm.bind_tools(all_nftclient_tools)
    
    # Create assistant instance 
    return Assistant(nftclient_runnable)


# Create entry node
enter_nftclient = create_entry_node("NFT Collection Specialist", "nftclient")


def route_nftclient(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    nftclient_safe_tools = get_specialist_safe_tools("nftclient")
    safe_toolnames = [t.name for t in nftclient_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "nftclient_safe_tools"
    return "nftclient_sensitive_tools"


def get_nftclient_safe_tool_node():
    """Create safe tool node for nftclient specialist"""
    safe_tools = get_specialist_safe_tools("nftclient")
    return ToolNode(safe_tools)


def get_nftclient_sensitive_tool_node():
    """Create sensitive tool node for nftclient specialist"""
    sensitive_tools = get_specialist_sensitive_tools("nftclient")
    return ToolNode(sensitive_tools)
