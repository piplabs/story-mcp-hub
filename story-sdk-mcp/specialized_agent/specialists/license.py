from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# License specialist prompt
license_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling License operations on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with license operations. "
     "Search for available license terms based on the user's preferences and confirm the licensing details with the customer. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a license operations operation isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_license_assistant():
    """Create license assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    license_safe_tools = get_specialist_safe_tools("license")
    license_sensitive_tools = get_specialist_sensitive_tools("license")
    
    # Combine with CompleteOrEscalate
    all_license_tools = license_safe_tools + license_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    license_runnable = license_prompt | llm.bind_tools(all_license_tools)
    
    # Create assistant instance 
    return Assistant(license_runnable)


# Create entry node
enter_license = create_entry_node("License Specialist", "license")


def route_license(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    license_safe_tools = get_specialist_safe_tools("license")
    safe_toolnames = [t.name for t in license_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "license_safe_tools"
    return "license_sensitive_tools"


def get_license_safe_tool_node():
    """Create safe tool node for license specialist"""
    safe_tools = get_specialist_safe_tools("license")
    return ToolNode(safe_tools)


def get_license_sensitive_tool_node():
    """Create sensitive tool node for license specialist"""
    sensitive_tools = get_specialist_sensitive_tools("license")
    return ToolNode(sensitive_tools)
