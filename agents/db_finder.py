# AGENT SEARCHES KAGGLE API VIA CLI in DOCKER
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import subprocess
from typing_extensions import TypedDict
from prompts import db_finder_plan_search_prompt, db_finder_loop_prompt, code_inter_kaggle_api
from main import cli_kaggle_docker, parse_subprocess_output, chat_invoke


class DBFinderState(TypedDict):
    messages: list[BaseMessage] = []
    query: str
    temp: dict
    loop_results: list[str] = []
    plan: str = ""



def agentic_loop(state: DBFinderState) -> DBFinderState:
    """
    This function is used to run the agentic loop. It will select between running kaggle api search, altering the temp dict in the state, or selecting a dataset (END).
    """
    
    while True:
        # only store the last 20 messages
        state['messages'] = state['messages'][-20:]

        # run the central message
        print("------------------------------------------------------- " + str(len(state['messages'])) + " -------------------------------------------------------")
        # print([str(m.content).strip() for m in state['messages'] if isinstance(m, BaseMessage)])
        central_msg = HumanMessage(content=
            db_finder_loop_prompt.format(
                query=state['query'], 
                plan_once="Be sure to plan your approach only once" if len(state['messages']) == 0 else "Here is your plan: " + state['plan'],
                temp=" ".join([f"{k}: {v}" for k, v in state['temp'].items()]),
                loop_stuck="You are stuck in a loop. Please try to change your action" if len(state['loop_results']) >= 2 and len(set(state['loop_results'][-3:])) == 1 else "",
            )
        )

        temp = state['messages']
        temp.append(central_msg)
        result_json = chat_invoke(temp, "json")
        print(result_json)
        state['messages'].pop(len(state['messages']) - 1)
    
        # add the messages to the state in a custom way
        state['messages'].append(HumanMessage(content="What is your action?"))
        state['messages'].append(AIMessage(content=str(result_json['action']) + " : " + str(result_json['reason'])))
        print(result_json['action'] + " : " + result_json['reason'])

        state['loop_results'].append(result_json['action'])

        # execute the actions
        if result_json['action'] == 'plan':
            state = plan(state)
        elif result_json['action'] == 'api':
            state = run_kaggle_api(state, result_json['details'])
        elif result_json['action'] == 'alter':
            state['temp'][result_json['details'].split(':')[0]] = result_json['details'].split(':')[1]
            print("temp: " + str(state['temp']))
        elif result_json['action'] == 'end':
            print("end: " + result_json['details'])
            return result_json['details']
        else:
            # send error to the messages 
            state['messages'].append(SystemMessage(content=f"Invalid action. Please try again. Here is the error: {str(e)}"))
            continue

def plan(state: DBFinderState) -> DBFinderState:
    """Plans the search for a dataset."""
    
    plan_msg = HumanMessage(content=
        db_finder_plan_search_prompt.format(query=state['query'], temp=" ".join([f"{k}: {v}" for k, v in state['temp'].items()]))
    )
    temp = state['messages']
    temp.append(plan_msg)
    result = chat_invoke(temp, "str")
    state['messages'].pop(len(state['messages']) - 1)
    state['messages'].append(AIMessage(content=result))
    print("plan: " + result)
    state['plan'] = result
    state['messages'].append(HumanMessage(content="Now that we have a plan, let's proceed with the search?"))

    return state

def run_kaggle_api(state: DBFinderState, task: str) -> DBFinderState:
    """Runs the kaggle api command in the code interpreter."""

    # use LLM to generate kaggle command based on the task
    msg = HumanMessage(content=code_inter_kaggle_api.format(
        task=task,
    ))

    temp = state['messages']
    temp.append(msg)
    result = chat_invoke(temp, "json")
    state['messages'].pop(len(state['messages']) - 1)
    kaggle_api_command = result['command']
    print("kaggle api command: ", kaggle_api_command)

    # run the kaggle api command
    out, _ = cli_kaggle_docker(kaggle_api_command)

    # parse the output of the kaggle api command
    out = parse_subprocess_output(out, "kaggle-api")
    print(out)

    # store the output in the message history
    if "error" in out.lower():
        state['messages'].append(SystemMessage(content="Here is the error. Use this to guide changes to the command: " + out))
    else:
        state['messages'].append(SystemMessage(content="Here is the output of the command: " + out))

    # return the state
    return state

# TESTING
agentic_loop(
    {
        'messages': [],
        'query': 'Find me a dataset of house prices in UAE and tell me which area has the highest house prices. Store the dataframe in memorya',
        'temp': {},
        'loop_results': [],
        'plan': ''
    }
) 
