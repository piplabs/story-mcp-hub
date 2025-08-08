from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition, ToolNode

from ..assistant import Assistant, llm
from ..tools import CompleteOrEscalate
from ..utils import create_entry_node
from ..state import State
from ..mcp_integration import get_specialist_safe_tools, get_specialist_sensitive_tools, get_all_specialist_tools


# Dispute specialist prompt
dispute_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a specialized assistant for handling IP disputes on Story Protocol. "
     "The primary assistant delegates work to you whenever the user needs "
     "help with disputes. "
     "Confirm the dispute details with the customer and inform them "
     "of any additional fees. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If you need more information or the customer changes their mind, "
     "escalate the task back to the main assistant."
     " Remember that a dispute isn't completed until after the relevant "
     "tool has successfully been used."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)


def create_dispute_assistant():
    """Create dispute assistant with MCP tools (called after MCP initialization)"""
    # Get actual MCP tools for this specialist
    dispute_safe_tools = get_specialist_safe_tools("dispute")
    dispute_sensitive_tools = get_specialist_sensitive_tools("dispute")
    
    # Combine with CompleteOrEscalate
    all_dispute_tools = dispute_safe_tools + dispute_sensitive_tools + [CompleteOrEscalate]
    
    # Create runnable with real MCP tools
    dispute_runnable = dispute_prompt | llm.bind_tools(all_dispute_tools)
    
    # Create assistant instance 
    return Assistant(dispute_runnable)


# Create entry node
enter_dispute = create_entry_node("Dispute Specialist", "dispute")


def route_dispute(state: State):
    """Route function for safe vs sensitive tools"""
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    
    # Get tool names from actual MCP tools
    dispute_safe_tools = get_specialist_safe_tools("dispute")
    safe_toolnames = [t.name for t in dispute_safe_tools]
    
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "dispute_safe_tools"
    return "dispute_sensitive_tools"


def get_dispute_safe_tool_node():
    """Create safe tool node for dispute specialist"""
    safe_tools = get_specialist_safe_tools("dispute")
    return ToolNode(safe_tools)


def get_dispute_sensitive_tool_node():
    """Create sensitive tool node for dispute specialist"""
    sensitive_tools = get_specialist_sensitive_tools("dispute")
    return ToolNode(sensitive_tools)