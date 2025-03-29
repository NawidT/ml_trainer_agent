import os
from langchain_openai.chat_models import ChatOpenAI
import subprocess
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser



chat = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])

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

# handles the planning and eval LLMs
# connects to the database_finder_agent and code_interpreter_agent
# stores the chat_history[list: BaseMessage] and key_facts[dict] 


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