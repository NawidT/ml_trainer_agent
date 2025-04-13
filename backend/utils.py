from langchain_openai.chat_models import ChatOpenAI
from langchain_ollama.chat_models import ChatOllama
import os
import subprocess
import pickle
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

chat_main = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])
chat_df = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])
chat_ci = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])
chat = ChatOllama(model="llama3.2:latest")

# utility functions
def chat_invoke(cur_message: BaseMessage, messages: list[BaseMessage], output_format: str = "json"):
    """
    This function is used to invoke the chat model. Seperate the chat session from message chain by passing new list in params.
    Handles type safety within the function.
    """

    # chat = chat_ollama if caller == "main" else chat_df if caller == "df" else chat_ci
    # ensure messages are maxxed at 20
    if len(messages) > 20:
        messages = messages[-20:]

    msgs = messages.copy()
    if output_format == "json":
        msgs.extend([system_message, cur_message])
        while True:
            # Add a system message to ensure JSON output
            system_message = SystemMessage(content="You must respond with valid JSON only. Do not include any text outside of the JSON structure.")
            resp = chat.invoke(msgs)
            try:
                return JsonOutputParser().parse(resp.content.strip())
            except Exception as e:
                msgs.append(SystemMessage(content="Error parsing JSON. Please try again. Invalid JSON object = " + resp.content.strip()))
                continue
    elif output_format == "str":
        chain = chat | StrOutputParser()
        return chain.invoke(messages + [cur_message])
    else:
        raise ValueError("Invalid output format. Please use 'json' or 'str'.")
 
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
    docker_compose_file = "{service}-1".format(service=compose_service)
    files = output.split("Attaching to " + docker_compose_file)[1].split("\n")
    files = [file.split("|")[1].strip() if file.startswith(docker_compose_file + "  |") else file 
             for file in files 
             if "exited" not in file and file != ""]
    return "\n".join(files)

def get_file_names(folder_name: str) -> list[str]:
    """Recursively grabs all files in a folder."""
    tmp_names = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            # if folder, add the folder name to the tmp_names
            if os.path.isdir(os.path.join(root, file)):
                folder_names = get_file_names(os.path.join(root, file))
                tmp_names.extend(folder_names)
            # if file, add the file name to the tmp_names
            else:
                tmp_names.append(os.path.join(root, file))
    return tmp_names

def get_memory_keys(mem_loc: str) -> str:
    """Grabs the memory variables from the pickle file."""
    try:
        # load the memory variables from the pickle file. The file is a dictionary with keys as variable names and values as variable values
        with open(mem_loc, 'rb') as f:
            memory_variables = pickle.load(f)
        # return the memory keys
        return ", ".join(list(memory_variables.keys())) if type(memory_variables) == dict else "memory variables not a dictionary. Invalid memory file."
    except Exception as e:
        return "memory file is empty as of now."