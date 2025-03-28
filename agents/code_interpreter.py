from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from db_finder import cli_kaggle_docker
import pickle
from main import chat
import subprocess
import os
import json
from prompts import code_inter_more_info, code_inter_init_prompt, code_inter_loop_prompt

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
        central_msg = HumanMessage(content=(code_inter_init_prompt 
                    if len(state['messages']) == 0 else code_inter_loop_prompt).format(
            user_query=state['user_query'],
            keys_of_mem=get_memory_keys(state),
            kv_pairs_facts= ", ".join([f"{k}: {v}" for k, v in state['facts'].items()])
        ))

        temp = state['messages']
        temp.append(central_msg)
        result = chat.invoke(temp)

        # check if the result is a valid json
        try:
            result_json = json.loads(result.content.strip())
        except Exception as e:
            print(result.content.strip())
            state['messages'].append(SystemMessage(content=f"Invalid JSON. Please try again. Here is the error: {str(e)}"))
            continue

        # add the messages to the state in a custom way
        state['messages'].append(HumanMessage(content="What is your action?"))
        state['messages'].append(AIMessage(content=str(result_json['action']) + " : " + str(result_json['reason'])))
        print(result_json['action'] + " : " + result_json['reason'])

        if result_json['action'] == 'run':
            state['code'] = result_json['details']['code']
            state['code_goal'] = result_json['details']['code_goal']
            state = run_code(state)
        elif result_json['action'] == 'store_fact':
            if result_json['details'] is not None and result_json['details']['fact'] is not None:
                state['facts'][result_json['details']['fact'].split(':')[0]] = result_json['details']['fact'].split(':')[1]
            else:
                state['messages'].append(SystemMessage(content="Invalid fact. Please try again."))
                continue
        elif result_json['action'] == 'end':
            if result_json['details'] is not None and result_json['details']['final_answer'] is not None:
                return result_json['details']['final_answer']
            else:
                state['messages'].append(SystemMessage(content="Invalid final answer. Please try again."))
                continue
        
        
        
def run_code(state: CodeInterpreterState) -> CodeInterpreterState:
    """Runs the code in the code interpreter and potentially stores the result in memory."""

    # pass the code thru another LLM with more detailed information and request changes
    more_info_msg = HumanMessage(content=code_inter_more_info.format(
        code=state['code'],
        facts_kv_pairs= ", ".join([f"{k}: {v}" for k, v in state['facts'].items()]),
        code_goal=state['code_goal'],
        memory_location=state['memory_location']
    ))

    temp = state['messages']
    temp.append(more_info_msg)
    result = chat.invoke(temp)
    generated_code = result.content.strip()
    state['messages'].pop(len(state['messages']) - 1)
    state['messages'].append(AIMessage(content=generated_code))

    if generated_code.startswith("```python"):
        generated_code = generated_code.replace("```python", "", 1)
    if generated_code.endswith("```"):
        generated_code = generated_code.rsplit("```", 1)[0]

    print(generated_code)

    # save the code in a python file (codespace.py)
    with open(state['code_file'], 'w') as f:
        f.write(generated_code)

    # run code via subprocess and running docker container
    interpreter = subprocess.run(
        ['docker-compose', '-f', 'dockercompose.yaml', 'up', '--build', '--remove-orphans', 'code-interpreter'],
        env=os.environ,
        capture_output=True,
        text=True,
        check=True
    )
    out, err = interpreter.stdout, interpreter.stderr
    out = parse_subprocess_output(out, "code-interpreter")
    print(out)

    # grab the output/findings of the code and store in message history
    state['messages'].append(AIMessage(content="Here is the output of the code: " + out))

    # return the state
    return state

def parse_subprocess_output(output: str, compose_service : str) -> str:
    """Parses the output of the subprocess and returns the output of the code."""
    docker_compose_file = "ml_trainer_agent-{service}-1".format(service=compose_service)
    files = output.split("Attaching to " + docker_compose_file)[1].split("\n")
    files = [file.split("|")[1].strip() if file.startswith(docker_compose_file + "  |") else file 
             for file in files 
             if "exited" not in file and file != ""]
    return "\n".join(files)

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
agentic_loop(
    {
        'messages': [],
        'code': '',
        'kaggle_file': 'marusagar/hand-gesture-detection-system',
        'user_query': '''Generate me a 20-list of house prices in Qatar and tell me which area has the highest house prices. Store the dataframe in memory''',
        'facts': {},
        'memory_location': 'tmp/memory.pkl', # use relative path since both in same directory (tmp)
        'code_file': 'tmp/codespace.py',
        'code_goal': ''
    }
)