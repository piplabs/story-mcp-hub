from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the dialog state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    wallet_address: str
    dialog_state: Annotated[
        list[
            Literal[
                "assistant",
                "dispute",
                "ipaccount", 
                "ipasset",
                "license",
                "nftclient",
                "royalty", 
                "wip"
            ]
        ],
        update_dialog_stack,
    ]