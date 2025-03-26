# AGENT SEARCHES KAGGLE API VIA CLI in DOCKER
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import json
from langgraph.graph import MessagesState, START, END, StateGraph
from langchain_core.tools import tool
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import subprocess
from typing_extensions import TypedDict
from prompts import kaggle_api_search_prompt, db_finder_plan_search_prompt, db_finder_loop_prompt    


chat = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])

class DBFinderState(TypedDict):
    messages: list[MessagesState]
    query: str
    temp: dict
    loop_results: list[str]


def agentic_loop(state: DBFinderState) -> str:
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
                plan_once="Be sure to plan your approach only once" if len(state['messages']) == 0 else "",
                temp=" ".join([f"{k}: {v}" for k, v in state['temp'].items()]),
                loop_stuck="You are stuck in a loop. Please try to change your action" if len(state['loop_results']) >= 2 and len(set(state['loop_results'][-3:])) == 1 else ""
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
            state = run_kaggle_api_search(state)
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

def plan(state: DBFinderState) -> str:
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

def run_kaggle_api_search(state: DBFinderState) -> str:
    """Searches the Kaggle API via the CLI for datasets matching the user's query."""

    # generate the kaggle api search command to be used kaggle datasets -s {query}
    instructions = HumanMessage(content=
        kaggle_api_search_prompt.format(query=state['query'])  
    )
    # temp is created to not add the instuction to messages everytime LLM is called
    temp = state['messages']
    temp.append(instructions)
    result = chat.invoke(temp)
    state['messages'].pop(len(state['messages']) - 1)
    state['messages'].append(AIMessage(content="generated command:" + result.content.strip()))
    print("generated command: " + result.content.strip())
    count = 0
    while True:
        if result.content is not None:
            state['query'] = result.content.strip()
            break
        else:
            # print(result.content.strip())
            result = chat.invoke(temp)
            count += 1
            if count > 3:
                raise ValueError('Invalid command')
    
    
    # set the query as an env var to be used by image when dockercompose is run
    os.environ['KAGGLE_COMMAND'] = state['query']

    # execute the command in a subprocess in a docker container
    try:
        # Run docker-compose up
        interpreter = subprocess.run(
            ['docker-compose', '-f', 'dockercompose.yaml', 'up', '--build', '--remove-orphans'],
            env=os.environ,
            capture_output=True,
            text=True,
            check=True
        )
        print(interpreter.stdout.split("#6 DONE 0.0s")[1])
    except subprocess.CalledProcessError as e:
        # create an SystemMessage with the error and return state
        state['messages'].append(SystemMessage(content=f"Most likely the generated query syntax is not valid. Please try again. Here is the error: {str(e.stderr)}"))
        print(f"Error running command: ", str(e.stderr))
        return state
    finally:
        # Clean up: Stop and remove containers
        subprocess.run(
            ['docker-compose', '-f', 'dockercompose.yaml', 'down'],
            capture_output=True
        )

    # add the interpreter result to the messages
    if interpreter.stdout is not None and interpreter.stdout.split("#6 DONE 0.0s")[1] is not None:
        in_res = interpreter.stdout.split("#6 DONE 0.0s")[1]
        if "error" in in_res.lower():
            state['messages'].append(SystemMessage(content=f"There was an error in the command or the command was not executed. Here is the error: {in_res}"))
        else:
            state['messages'].append(AIMessage(content=in_res))
    else:
        raise ValueError('No valid result from kaggle api search. There was an error in the command or the command was not executed.')
    
    return state

agentic_loop(
    {
        'messages': [],
        'query': 'house prices in Canada',
        'temp': {},
        'loop_results': []
    }
)



   
    
