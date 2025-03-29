import os
from langchain_openai.chat_models import ChatOpenAI
import subprocess
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from agents.db_finder import agentic_loop as db_finder_agentic_loop, DBFinderState
from agents.code_interpreter import agentic_loop as code_inter_agentic_loop, CodeInterpreterState


# LLM
chat = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])

# adding initial states for persistence throughout main loop
db_finder_state = DBFinderState(
    messages=[],
    query="",
    temp={},
    loop_results=[],
    plan=""
)

code_inter_state = CodeInterpreterState(
    messages=[],
    user_query="",
    code="",
    temp={},
    facts={},
    memory_location="tmp/memory.pkl",
    code_file="tmp/codespace.py",
    plan=""
)


# utility functions
def chat_invoke(messages: list[BaseMessage], output_format: str = "json") -> str:
    """
    This function is used to invoke the chat model.
    """
    if output_format == "json":
        chain = chat | JsonOutputParser()
    elif output_format == "str":
        chain = chat | StrOutputParser()
    else:
        raise ValueError("Invalid output format. Please use 'json' or 'str'.")
    return chain.invoke(messages)
 
def cli_kaggle_docker(command: str) -> str:
    """
    This function is used to run the kaggle api in the custom docker container.
    """
    # set the command as an env var to be used by image when dockercompose is run
    os.environ['KAGGLE_COMMAND'] = command

    # Run docker-compose up
    interpreter = subprocess.run(
        ['docker-compose', '-f', 'dockercompose.yaml', 'up', '--build', '--remove-orphans', 'kaggle-api'],
        env=os.environ,
        capture_output=True,
        text=True,
        check=True
    )
    return interpreter.stdout, interpreter.stderr

def parse_subprocess_output(output: str, compose_service : str) -> str:
    """Parses the output of the subprocess and returns the output of the code."""
    docker_compose_file = "ml_trainer_agent-{service}-1".format(service=compose_service)
    files = output.split("Attaching to " + docker_compose_file)[1].split("\n")
    files = [file.split("|")[1].strip() if file.startswith(docker_compose_file + "  |") else file 
             for file in files 
             if "exited" not in file and file != ""]
    return "\n".join(files)


class MainState(TypedDict):
    messages: list[BaseMessage]
    user_query: str


def main(state: MainState):
    """
    This function is used to run the main loop.
    """

    while True:
        stage_one_msg = HumanMessage(content="""
            You are a helpful manager who controls two assistants.
            The first assistant is a database_finder_agent that is a kaggle api expert.
            The second assistant is a code_interpreter_agent that is a python programmer.
            You will be given a user query.
            
            user query : {user_query}                       

            RETURN IN THE FOLLOWING FORMAT:
            {{
            "assistant": "database_finder_agent" | "code_interpreter_agent" | "END",
            "details": "details of the exact action the assistant needs to take"
            "reason": "reason for choosing the assistant or ending"
            }}                        
            
        """.format(user_query=state['user_query']))

        temp = state['messages'].copy()
        temp.append(stage_one_msg)
        stage_one_json = chat_invoke(temp, "json")
        print(stage_one_json)


        stage_two_msg = HumanMessage(content="""
            Your task is to audit the work of the manager and grade its work to make sure it made the best possible decision.
            
            grading scale : 1 being the worst and 5 being the best.
            chat history : {chat_history}
            user query : {user_query}
            manager's decision : {manager_decision}
                                    
            RETURN IN THE FOLLOWING FORMAT:
            {{
            "grade": "1" | "2" | "3" | "4" | "5",
            "reason": "reason for the grade"
            }}                        
        """.format(
            chat_history=state['chat_history'], user_query=state['user_query'], 
            manager_decision=stage_one_json['assistant'] + " -> " + stage_one_json['reason']
        ))

        stage_two_json = chat_invoke([stage_two_msg], "json")
        grade = int(stage_two_json['grade'])
        print(stage_two_json['reason'])

        if grade < 3:
            state['messages'].append(SystemMessage(content="The manager made a bad decision. Please try again."))
            continue
        else:
            state['messages'].append(SystemMessage(content=f"The manager made a good decision. {stage_one_json['details']}"))
            print("-----------------------------------" + stage_one_json['assistant'] + "-----------------------------------")
            if stage_one_json['assistant'] == "database_finder_agent":
                db_finder_state['query'] = stage_one_json['details']
                db_finder_state['plan'] = ""
                db_finder_state, findings = db_finder_agentic_loop(db_finder_state)
                state['messages'].append(HumanMessage(content="Here are the findings from the database_finder_agent: " + findings))
            elif stage_one_json['assistant'] == "code_interpreter_agent":
                code_inter_state['user_query'] = stage_one_json['details']
                code_inter_state, findings = code_inter_agentic_loop(code_inter_state)
                state['messages'].append(HumanMessage(content="Here are the findings from the code_interpreter_agent: " + findings))
            elif stage_one_json['assistant'] == "END":
                print(" ENDING REASON : " + stage_one_json['reason'])
                return stage_one_json['reason']


main(
    {
        'chat_history': [],
        'user_query': 'Find me a dataset of house prices in UAE and store it locally in tmp folder'
    }
)