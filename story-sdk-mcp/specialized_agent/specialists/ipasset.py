from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# IP Asset specialist prompt
ipasset_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling IP Asset operations on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with ip asset operations. "
     "Confirm the IP asset details with the customer and inform them of any additional fees or requirements. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a ip asset operations operation isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_ipasset_assistant():
    """Create ipasset assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    ipasset_safe_tools = get_specialist_safe_tools("ipasset")
    ipasset_sensitive_tools = get_specialist_sensitive_tools("ipasset")
    
    # Combine with CompleteOrEscalate
    all_ipasset_tools = ipasset_safe_tools + ipasset_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    ipasset_runnable = ipasset_prompt | llm.bind_tools(all_ipasset_tools)
    
    # Create assistant instance 
    return Assistant(ipasset_runnable)


# Create entry node
enter_ipasset = create_entry_node("IP Asset Specialist", "ipasset")


def route_ipasset(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    ipasset_safe_tools = get_specialist_safe_tools("ipasset")
    safe_toolnames = [t.name for t in ipasset_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "ipasset_safe_tools"
    return "ipasset_sensitive_tools"


def get_ipasset_safe_tool_node():
    """Create safe tool node for ipasset specialist"""
    safe_tools = get_specialist_safe_tools("ipasset")
    return ToolNode(safe_tools)


def get_ipasset_sensitive_tool_node():
    """Create sensitive tool node for ipasset specialist"""
    sensitive_tools = get_specialist_sensitive_tools("ipasset")
    return ToolNode(sensitive_tools)
