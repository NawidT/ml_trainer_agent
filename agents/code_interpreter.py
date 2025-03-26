from kagglehub import KaggleDatasetAdapter
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from db_finder import cli_kaggle_docker
import pickle
import pandas as pd
from main import chat

class CodeInterpreterState(TypedDict):
    messages: list[BaseMessage]
    code: str
    kaggle_file: str
    memory_location: str = "tmp/memory.pkl" # this stores memory in pickle file, can be accessed by generated subprocess
    facts: dict[str, str] = {}
    code_file: str = "codespace.py"
    query: str

def get_memory_keys(state: CodeInterpreterState) -> str:
    """Grabs the memory variables from the pickle file."""

    # load the memory variables from the pickle file. The file is a dictionary with keys as variable names and values as variable values
    with open(state['memory_location'], 'rb') as f:
        memory_variables = pickle.load(f)
    # return the memory keys
    return ", ".join(list(memory_variables.keys())) if type(memory_variables) == dict else "memory variables not a dictionary. Invalid memory file."

def agentic_loop(state: CodeInterpreterState) -> CodeInterpreterState:
    """
    This function is used to run the agentic loop. 
    We will give the LLM access to the following:
    - the user's query
    - memory (to store object based information)
    - facts (to store string based information)

    LLM can choose the following actions:
    - run code
    - get kaggle data
    - store a fact
    - store an object in memory
    - END (return the final answer)
    """

    while True:
        central_msg = HumanMessage(content="""
            You are an assistant that helps your user get closer to {user_query}
            You have access to the following information:
            - memory: {keys_of_mem} (for storing and accessing Python objects)
            - facts: {keys_of_facts} (for storing string-based information)
            - previous messages above

            You can perform the following actions:
            - run: execute Python code and store results
            - get_data: download and extract a Kaggle dataset
            - store_fact: save a string fact for later reference
            - end: return final answer (END)

            RETURN IN THE FOLLOWING FORMAT:
            {{
                "action": "run" | "get_data" | "store_fact" | "end",
                "details": {{
                    "code": "Python code to run" | null,
                    "dataset": "Kaggle dataset reference" | null, 
                    "fact": "Return in format key: value" | null,
                    "final_answer": "Answer to return" | null
                }},
                "reason": "Explanation for taking this action"
            }}
        """.format(
            user_query=state['user_query'],
            keys_of_mem=get_memory_keys(state),
            keys_of_facts= ", ".join(list(state['facts'].keys()))
        ))
        
def run_code(state: CodeInterpreterState) -> CodeInterpreterState:
    """Runs the code in the code interpreter and potentially stores the result in memory."""

    # pass the code thru another LLM with more detailed information and request changes
    more_info_msg = HumanMessage(content="""
        Currently the Python code you have is: {code}
       
        To access a memory variable, here's the syntax:
        - tmp_dict = pickle.load(open('tmp/memory.pkl', 'rb'))
        - tmp_dict['variable_name']

        To store a result in memory, here's the syntax:
        - tmp_dict['variable_name'] = result
        - pickle.dump(tmp_dict, open('tmp/memory.pkl', 'wb'))
       
       Here are the packages you can use: [pandas, numpy, scikit-learn]
       Here are the facts you have: {facts_kv_pairs}

       Please rewrite the code factoring the above information to guide you towards the user's query: {user_query}
       RETURN ONLY THE CODE AS A STRING
    """
    )

    temp = state['messages']
    temp.append(more_info_msg)
    result = chat.invoke(temp)
    state['messages'].pop(len(state['messages']) - 1)
    state['messages'].append(AIMessage(content=result.content.strip()))

    # save the code in a python file (codespace.py)
    with open(state['code_file'], 'w') as f:
        f.write(result.content.strip())
    # run code via subprocess and running docker container
    out, err = cli_kaggle_docker("python " + state['code_file'])
    # grab the output/findings of the code and store in message history

    # return the state
    return state


def idk(state: CodeInterpreterState) -> CodeInterpreterState:
    """Runs the code in the code interpreter."""

    # find the files from the kaggle dataset and choose the best one
    out, err = cli_kaggle_docker("kaggle datasets files -v " + state['kaggle_file'])
    
    files = out.split("Attaching to ml_trainer_agent-kaggle-api-1")[1].split("\n")
    files = [file.split("|")[1].strip() if file.startswith("ml_trainer_agent-kaggle-api-1  |") else file 
             for file in files 
             if "exited" not in file and file != ""]
    print(files)

    """
    There's a couple things to handle here:
    - We want to store the directory structure of the kaggle dataset, for future retrieval
    """
    # df = pd.read_csv(files[0])
    # print(df.head())
    # download the dataset
    # kaggle datasets download -p kaggle_file --unzip juhibhojani/house-price
    # preset a couple memory variables e.g. pyspark_df
    # df = pd.read_csv("kaggle_file/house_prices.csv")
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
        'kaggle_file': 'marusagar/hand-gesture-detection-system'
    }
)