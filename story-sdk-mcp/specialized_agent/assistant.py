import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from dotenv import load_dotenv
from pathlib import Path
from .state import State

# Load environment variables from .env file in the project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            # Ensure wallet_address is available for template formatting
            invoke_state = {
                **state,
                "wallet_address": state.get("wallet_address", "Not provided")
            }
            result = self.runnable.invoke(invoke_state)
            # If the LLM happens to return an empty response, we will re-prompt
            # it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


# Initialize LLM - using OpenAI GPT-4
# The API key will be loaded from OPENAI_API_KEY environment variable
llm = ChatOpenAI(
    model="gpt-4o",  # Latest GPT-4 Omni model, you can also use "gpt-4-turbo", "gpt-4", or "gpt-3.5-turbo"
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)