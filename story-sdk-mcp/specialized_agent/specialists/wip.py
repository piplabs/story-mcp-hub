from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# WIP Token specialist prompt
wip_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling WIP (Wrapped IP) token operations on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with wip (wrapped ip) token operations. "
     "Search for available WIP options based on the user's preferences and confirm the token details with the customer. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a wip (wrapped ip) token operations operation isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_wip_assistant():
    """Create wip assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    wip_safe_tools = get_specialist_safe_tools("wip")
    wip_sensitive_tools = get_specialist_sensitive_tools("wip")
    
    # Combine with CompleteOrEscalate
    all_wip_tools = wip_safe_tools + wip_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    wip_runnable = wip_prompt | llm.bind_tools(all_wip_tools)
    
    # Create assistant instance 
    return Assistant(wip_runnable)


# Create entry node
enter_wip = create_entry_node("WIP Token Specialist", "wip")


def route_wip(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    wip_safe_tools = get_specialist_safe_tools("wip")
    safe_toolnames = [t.name for t in wip_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "wip_safe_tools"
    return "wip_sensitive_tools"


def get_wip_safe_tool_node():
    """Create safe tool node for wip specialist"""
    safe_tools = get_specialist_safe_tools("wip")
    return ToolNode(safe_tools)


def get_wip_sensitive_tool_node():
    """Create sensitive tool node for wip specialist"""
    sensitive_tools = get_specialist_sensitive_tools("wip")
    return ToolNode(sensitive_tools)
