from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import tools_condition
from pydantic import BaseModel, Field

from .assistant import Assistant, llm
from .state import State


# Primary assistant routing tools
class ToDisputeAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle dispute operations."""
    request: str = Field(
        description="Any necessary followup questions the dispute assistant should clarify before proceeding."
    )


class ToIPAccountAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle IP account operations."""
    request: str = Field(
        description="Any necessary followup questions the IP account assistant should clarify before proceeding."
    )


class ToIPAssetAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle IP asset operations."""
    request: str = Field(
        description="Any necessary followup questions the IP asset assistant should clarify before proceeding."
    )


class ToLicenseAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle license operations."""
    request: str = Field(
        description="Any necessary followup questions the license assistant should clarify before proceeding."
    )


class ToNFTClientAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle NFT collection operations."""
    request: str = Field(
        description="Any necessary followup questions the NFT collection assistant should clarify before proceeding."
    )


class ToRoyaltyAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle royalty operations."""
    request: str = Field(
        description="Any necessary followup questions the royalty assistant should clarify before proceeding."
    )


class ToWIPAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle WIP token operations."""
    request: str = Field(
        description="Any necessary followup questions the WIP token assistant should clarify before proceeding."
    )


# Primary assistant prompt
primary_assistant_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful customer support assistant for Story Protocol. "
     "Use the provided tools to search for information and assist the user's queries. "
     "When searching, be persistent. Expand your query bounds if the "
     "first search returns no results. "
     "If a search comes up empty, expand your search before giving up."
     "\n\nCurrent user wallet address: {wallet_address}\n"
     "\nCurrent time: {time}.",
     ),
    ("placeholder", "{messages}"),
]).partial(time=datetime.now)

# Available routing tools
primary_assistant_tools = [
    ToDisputeAssistant,
    ToIPAccountAssistant,
    ToIPAssetAssistant,
    ToLicenseAssistant,
    ToNFTClientAssistant,
    ToRoyaltyAssistant,
    ToWIPAssistant,
]

# Create runnable
assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools
)

# Create assistant instance 
primary_assistant = Assistant(assistant_runnable)


def route_primary_assistant(state: State):
    route = tools_condition(state)
    if route == "END":
        return "END"
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToDisputeAssistant.__name__:
            return "enter_dispute"
        elif tool_calls[0]["name"] == ToIPAccountAssistant.__name__:
            return "enter_ipaccount"
        elif tool_calls[0]["name"] == ToIPAssetAssistant.__name__:
            return "enter_ipasset"
        elif tool_calls[0]["name"] == ToLicenseAssistant.__name__:
            return "enter_license"
        elif tool_calls[0]["name"] == ToNFTClientAssistant.__name__:
            return "enter_nftclient"
        elif tool_calls[0]["name"] == ToRoyaltyAssistant.__name__:
            return "enter_royalty"
        elif tool_calls[0]["name"] == ToWIPAssistant.__name__:
            return "enter_wip"
        return "primary_assistant_tools"
    raise ValueError("Invalid route")