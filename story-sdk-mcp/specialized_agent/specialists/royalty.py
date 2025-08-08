from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# Royalty specialist prompt
royalty_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling Royalty operations on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with royalty operations. "
     "Search for available royalty options based on the user's preferences and confirm the royalty details with the customer. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a royalty operations operation isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_royalty_assistant():
    """Create royalty assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    royalty_safe_tools = get_specialist_safe_tools("royalty")
    royalty_sensitive_tools = get_specialist_sensitive_tools("royalty")
    
    # Combine with CompleteOrEscalate
    all_royalty_tools = royalty_safe_tools + royalty_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    royalty_runnable = royalty_prompt | llm.bind_tools(all_royalty_tools)
    
    # Create assistant instance 
    return Assistant(royalty_runnable)


# Create entry node
enter_royalty = create_entry_node("Royalty Specialist", "royalty")


def route_royalty(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    royalty_safe_tools = get_specialist_safe_tools("royalty")
    safe_toolnames = [t.name for t in royalty_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "royalty_safe_tools"
    return "royalty_sensitive_tools"


def get_royalty_safe_tool_node():
    """Create safe tool node for royalty specialist"""
    safe_tools = get_specialist_safe_tools("royalty")
    return ToolNode(safe_tools)


def get_royalty_sensitive_tool_node():
    """Create sensitive tool node for royalty specialist"""
    sensitive_tools = get_specialist_sensitive_tools("royalty")
    return ToolNode(sensitive_tools)
