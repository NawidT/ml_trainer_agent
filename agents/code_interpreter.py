import kagglehub
from typing_extensions import TypedDict
from langgraph.graph import MessagesState
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import subprocess
import pickle


class CodeInterpreterState(TypedDict):
    messages: list[MessagesState]
    code: str
    memory_location: str = "tmp/memory.pkl" # this stores memory in pickle file, can be accessed by generated subprocess
    
def run_code(state: CodeInterpreterState) -> CodeInterpreterState:
    """Runs the code in the code interpreter."""


    # generate the code

    # write the code to a tmp file

    # run a subprocess from the docker container

    # add the result to the messages

    # return the state
    return state

# # TESTING

run_code(
    {
        'messages': [],
        'code': 'print("hello")'
    }
)