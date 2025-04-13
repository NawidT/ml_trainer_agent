import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import subprocess
import os
import pickle

from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from utils import parse_subprocess_output, chat_invoke  
from prompts import code_inter_run_code, code_inter_init_prompt, code_inter_loop_prompt

class CodeInterpreterState(TypedDict):
    messages: list[BaseMessage]
    code: str
    memory_location: str = "tmp/memory.pkl" # this stores memory in pickle file, can be accessed by generated subprocess
    facts: dict[str, str] = {}
    code_file: str = "tmp/codespace.py"
    query: str
    plan: str = ""

def get_memory_keys(state: CodeInterpreterState) -> str:
    """Grabs the memory variables from the pickle file."""

    try:
        # load the memory variables from the pickle file. The file is a dictionary with keys as variable names and values as variable values
        with open(state['memory_location'], 'rb') as f:
            memory_variables = pickle.load(f)
        # return the memory keys
        return ", ".join(list(memory_variables.keys())) if type(memory_variables) == dict else "memory variables not a dictionary. Invalid memory file."
    except Exception as e:
        return "memory file is empty as of now."

def agentic_loop(state: CodeInterpreterState) -> CodeInterpreterState:
    """
    This function is used to run the agentic loop. 
    We will give the LLM access to the following:
    - the user's query
    - memory (to store object based information)
    - facts (to store string based information)

    LLM can choose the following actions:
    - run code
    - store a fact
    - store an object in memory
    - END (return the final answer)
    """

    while True:
        # only store the last 20 messages
        state['messages'] = state['messages'][-20:]

        tmp_folder = ["tmp/tmp/" + e for e in os.listdir("./tmp/tmp")] + [state['memory_location'], state['code_file']]

        central_msg = HumanMessage(content=(code_inter_init_prompt 
                    if len(state['messages']) == 0 else code_inter_loop_prompt).format(
            user_query=state['user_query'],
            keys_of_mem=get_memory_keys(state),
            kv_pairs_facts= ", ".join([f"{k}: {v}" for k, v in state['facts'].items()]),
            plan=state['plan'],
            tmp_folder=tmp_folder
        ))

        temp = state['messages'].copy()
        temp.append(central_msg)
        try:
            result_json = chat_invoke(temp, "json", "ci")
        except Exception as e:
            print(e)
            state['messages'].append(HumanMessage(content="Error in outputting json: " + str(e)))
            continue

        # add the messages to the state in a custom way
        state['messages'].append(HumanMessage(content="What is your action?"))
        state['messages'].append(AIMessage(content=str(result_json['action']) + " : " + str(result_json['reason'])))
        print(result_json['action'] + " : " + result_json['reason'])

        if result_json['action'] == 'run':
            state['code_goal'] = result_json['details']['code_goal']
            state = run_code(state, state['code_goal'])
        elif result_json['action'] == 'store_fact':
            if result_json['details'] is not None and result_json['details']['fact'] is not None and type(result_json['details']['fact']) == str:
                state = store_fact(state, result_json['details']['fact'])
            else:
                state['messages'].append(SystemMessage(content="Invalid fact. Please try again."))
                continue
        elif result_json['action'] == 'plan':
            state = plan(state)
        elif result_json['action'] == 'end':
            if result_json['details'] is not None and result_json['details']['final_answer'] is not None:
                return state, result_json['details']['final_answer']
            else:
                state['messages'].append(SystemMessage(content="Invalid final answer. Please try again."))
                continue
        
def plan(state: CodeInterpreterState) -> CodeInterpreterState:
    """Plans the search for the kaggle dataset."""

    # use LLM to generate a plan for the search
    msg = HumanMessage(content="Based on the above messages, use this space to write a short plan for your thoughts to proceed with the next steps.")
    temp = state['messages']
    temp.append(msg)
    result = chat_invoke(temp, "str", "ci")
    state['messages'].pop(len(state['messages']) - 1)
    state['messages'].append(AIMessage(content=result))

    # add the plan to the state and it will be used in future loop messages until plan changes
    state['plan'] = result

    # return the state
    return state
        
        
def run_code(state: CodeInterpreterState, code_goal: str) -> CodeInterpreterState:
    """Runs the code in the code interpreter and potentially stores the result in memory."""

    # pass the code thru another LLM with more detailed information and request changes
    tmp_folder = ["tmp/tmp/" + e for e in os.listdir("./tmp/tmp")] + ["tmp/memory.pkl", "tmp/codespace.py"]
    print(tmp_folder)
    more_info_msg = HumanMessage(content=code_inter_run_code.format(
        facts_kv_pairs= ", ".join([f"{k}: {v}" for k, v in state['facts'].items()]),
        code_goal=code_goal,
        memory_location=state['memory_location'],
        tmp_folder=tmp_folder
    ))

    temp = state['messages']
    temp.append(more_info_msg)
    generated_code = chat_invoke(temp, "str", "ci")
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
    try:
        out, _ = interpreter.stdout, interpreter.stderr
        out = parse_subprocess_output(out, "code-interpreter")
        print(out)
    except Exception as e:
        print(e)
        state['messages'].append(SystemMessage(content="Error running code. Please try again. " + str(e)))
        return state
    # grab the output/findings of the code and store in message history
    state['messages'].append(SystemMessage(content="Here is the output of the code: " + out))

    # return the state
    return state


def store_fact(state: CodeInterpreterState, fact: str) -> CodeInterpreterState:
    """Stores the fact in the state."""

    # rewrite the fact string as a key:value pair
    msg = HumanMessage(content=f"""
        Using the following information, convert the fact into a key:value pair. 
        fact: {fact}.
        Make sure the key is unique. Here are the existing keys: {state['facts'].keys()}.
        RETURN ONLY THE KEY:VALUE PAIR AS A STRING
    """)

    kv_pair = chat_invoke([msg], "str", "ci")
    print(kv_pair)

    # add the fact to the state
    state['facts'][kv_pair.split(':')[0]] = kv_pair.split(':')[1]

    # show all the facts
    print(state['facts'])
    return state

# TESTING
agentic_loop(
    {
        'messages': [],
        'code': '',
        'user_query': '''On the exisiting dataset, find me the top 10 most expensive properties in UAE''',
        'facts': {},
        'memory_location': 'tmp/memory.pkl', # use relative path since both in same directory (tmp)
        'code_file': 'tmp/codespace.py',
        'plan': ''
    }
)