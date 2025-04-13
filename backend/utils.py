from langchain_openai.chat_models import ChatOpenAI
from langchain_ollama.chat_models import ChatOllama
import os
import subprocess
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

chat_main = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])
chat_df = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])
chat_ci = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])
chat_ollama = ChatOllama(model="llama3.2:latest")

# utility functions
def chat_invoke(cur_message: BaseMessage, messages: list[BaseMessage], output_format: str = "json", caller: str = "main") -> str:
    """
    This function is used to invoke the chat model. Seperate the chat session from message chain by passing new list in params.

    """

    chat = chat_ollama if caller == "main" else chat_df if caller == "df" else chat_ci

    if output_format == "json":
        chain = chat | JsonOutputParser()
    elif output_format == "str":
        chain = chat | StrOutputParser()
    else:
        raise ValueError("Invalid output format. Please use 'json' or 'str'.")
    return chain.invoke(messages + [cur_message])
 
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