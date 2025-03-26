import kagglehub
from kagglehub import KaggleDatasetAdapter
from typing_extensions import TypedDict
from langgraph.graph import MessagesState
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from db_finder import cli_kaggle_docker
import pickle
import pandas as pd


class CodeInterpreterState(TypedDict):
    messages: list[MessagesState]
    code: str
    kaggle_file: str
    memory_location: str = "tmp/memory.pkl" # this stores memory in pickle file, can be accessed by generated subprocess
    
def get_memory_variables(state: CodeInterpreterState) -> CodeInterpreterState:
    """Grabs the memory variables from the pickle file."""

    # load the memory variables from the pickle file. The file is a dictionary with keys as variable names and values as variable values
    with open(state['memory_location'], 'rb') as f:
        memory_variables = pickle.load(f)

    # return the memory variables
    var_list = ", ".join(list(memory_variables.keys())) if type(memory_variables) == dict else "memory variables not a dictionary. Invalid memory file."
    return var_list


def run_code(state: CodeInterpreterState) -> CodeInterpreterState:
    """Runs the code in the code interpreter."""

    # find the files from the kaggle dataset and choose the best one

    # download the dataset
    # kaggle datasets download -p kaggle_file --unzip juhibhojani/house-price

    # preset a couple memory variables e.g. pyspark_df
    df = pd.read_csv("kaggle_file/house_prices.csv")
    

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
        'code': 'print("hello")',
        'kaggle_file': 'juhibhojani/house-price'
    }
)