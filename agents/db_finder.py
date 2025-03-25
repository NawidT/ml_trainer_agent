# AGENT SEARCHES KAGGLE API VIA CLI in DOCKER
import kaggle
from langgraph.graph import MessagesState, START, END, StateGraph
from langchain_core.tools import tool
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import subprocess
from typing_extensions import TypedDict
import os


class DBFinderState(TypedDict):
    messages: list[MessagesState]
    query: str

@tool
def run_kaggle_api_search(state: DBFinderState) -> str:
    """Searches the Kaggle API via the CLI for datasets matching the user's query."""

    # generate the kaggle api search command to be used kaggle datasets -s {query}
    prompt = ChatPromptTemplate.from_template(
        "Search the Kaggle API for datasets matching the user's query: {query}"
    )
    chain = prompt | ChatOpenAI(model="gpt-4o-mini")
    result = chain.invoke({"query": state['query']})
    print(result)


    state['query'] = 'kaggle datasets -s ' + 'diabetes'

    # set the query as an env var to be used by image when dockercompose is run
    os.environ['KAGGLE_COMMAND'] = state['query']

    # execute the command in a subprocess in a docker container
    try:
        # Run docker-compose up
        result = subprocess.run(
            ['docker-compose', '-f', 'dockercompose.yaml', 'up', '--build', '--remove-orphans'],
            env=os.environ,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Error output: {e.stderr}")
        raise
    finally:
        # Clean up: Stop and remove containers
        subprocess.run(
            ['docker-compose', '-f', 'dockercompose.yaml', 'down'],
            capture_output=True
        )

run_kaggle_api_search(
    {
        'messages': [],
        'query': ''
    }
)



   
    
