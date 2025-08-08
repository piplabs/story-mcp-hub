from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# IP Account specialist prompt
ipaccount_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling IP Account operations on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with ip account operations. "
     "Search for available tokens based on the user's preferences and confirm the details with the customer. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a ip account operations operation isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_ipaccount_assistant():
    """Create ipaccount assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    ipaccount_safe_tools = get_specialist_safe_tools("ipaccount")
    ipaccount_sensitive_tools = get_specialist_sensitive_tools("ipaccount")
    
    # Combine with CompleteOrEscalate
    all_ipaccount_tools = ipaccount_safe_tools + ipaccount_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    ipaccount_runnable = ipaccount_prompt | llm.bind_tools(all_ipaccount_tools)
    
    # Create assistant instance 
    return Assistant(ipaccount_runnable)


# Create entry node
enter_ipaccount = create_entry_node("IP Account Specialist", "ipaccount")


def route_ipaccount(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    ipaccount_safe_tools = get_specialist_safe_tools("ipaccount")
    safe_toolnames = [t.name for t in ipaccount_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "ipaccount_safe_tools"
    return "ipaccount_sensitive_tools"


def get_ipaccount_safe_tool_node():
    """Create safe tool node for ipaccount specialist"""
    safe_tools = get_specialist_safe_tools("ipaccount")
    return ToolNode(safe_tools)


def get_ipaccount_sensitive_tool_node():
    """Create sensitive tool node for ipaccount specialist"""
    sensitive_tools = get_specialist_sensitive_tools("ipaccount")
    return ToolNode(sensitive_tools)
