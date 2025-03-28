# AGENT SEARCHES KAGGLE API VIA CLI in DOCKER
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import subprocess
from typing_extensions import TypedDict
from prompts import kaggle_api_search_prompt, db_finder_plan_search_prompt, db_finder_loop_prompt    
from main import chat, cli_kaggle_docker, parse_subprocess_output


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
                plan_once="Be sure to plan your approach only once" 
                    if len(state['messages']) == 0 else "Here is your plan: " + state['plan'],
                temp=" ".join([f"{k}: {v}" for k, v in state['temp'].items()]),
                loop_stuck="You are stuck in a loop. Please try to change your action" if len(state['loop_results']) >= 2 and len(set(state['loop_results'][-3:])) == 1 else "",
            )
        )

        temp = state['messages']
        temp.append(central_msg)
        result = chat.invoke(temp)
        state['messages'].pop(len(state['messages']) - 1)

        # cleanup the result
        if result.content.startswith('```json'):
            result.content = result.content.replace('```json', '', 1)
        if result.content.startswith('```'):
            result.content = result.content.replace('```', '', 1)
        if result.content.endswith('```'):
            result.content = result.content.rsplit('```', 1)[0]

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

        state['loop_results'].append(result_json['action'])

        # execute the actions
        if result_json['action'] == 'plan':
            state = plan(state)
        elif result_json['action'] == 'search':
            state['query'] = result_json['details']
            state = run_kaggle_api(state, kaggle_api_search_prompt)
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
    result = chat.invoke(temp)
    state['messages'].pop(len(state['messages']) - 1)
    state['messages'].append(AIMessage(content=result.content.strip()))
    print("plan: " + result.content.strip())
    state['messages'].append(HumanMessage(content="Now that we have a plan, let's proceed with the search?"))

    return state

def run_kaggle_api(state: dict, prompt: str) -> dict:
    """Runs the kaggle api search command."""

    # generate the kaggle api search command to be used kaggle datasets -s {query}
    instructions = HumanMessage(content=
        prompt.format(query=state['query'])  
    )
    
    # temp is created to not add the instuction to messages everytime LLM is called
    temp = state['messages']
    temp.append(instructions)
    result = chat.invoke(temp)
    state['messages'].pop(len(state['messages']) - 1)
    generated_command = result.content.strip()
    state['messages'].append(AIMessage(content="generated command:" + generated_command))
    print("generated command: " + generated_command)

    # execute the command in a subprocess in a docker container
    try:
        stdout, _ = cli_kaggle_docker(generated_command)
        parsed_stdout = parse_subprocess_output(stdout, "kaggle-api")
    except Exception as e:
        # create an SystemMessage with the error and return state
        state['messages'].append(SystemMessage(content=f"Most likely the generated query syntax is not valid. Please try again. Here is the error: {str(e)}"))
        print(f"Error running command: ", str(e))
        return state
    finally:
        # Clean up: Stop and remove containers
        subprocess.run(
            ['docker-compose', '-f', 'dockercompose.yaml', 'down'],
            capture_output=True
        )

    # add the interpreter result to the messages
    state['messages'].append(SystemMessage(content=f"Here is the output of the command: {parsed_stdout}"))
    
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
