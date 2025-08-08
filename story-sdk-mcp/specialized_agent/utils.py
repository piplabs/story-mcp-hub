from typing import Callable
from langchain_core.messages import ToolMessage
from .state import State


def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    """Create an entry node for each workflow, stating the current assistant is <assistant_name>."""
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect "
                    "on the above conversation between the host assistant and the user. "
                    f"The user's intent is unsatisfied. Use the provided tools "
                    f"to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete "
                    "until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other "
                    "tasks, call the CompleteOrEscalate function to let the primary host assistant "
                    "take control."
                    " Do not mention who you are - just act as the proxy for the "
                    "assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }
    return entry_node