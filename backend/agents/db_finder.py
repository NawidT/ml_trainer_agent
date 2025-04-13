# AGENT SEARCHES KAGGLE API VIA CLI in DOCKER
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import subprocess
from typing_extensions import TypedDict
from prompts import db_finder_plan_search_prompt, db_finder_loop_prompt, db_finder_kaggle_api
from utils import cli_kaggle_docker, parse_subprocess_output, chat_invoke, get_file_names


class DBFinder:
    def __init__(self, messages=None, query="", temp=None, plan=""):
        """Initialize the DBFinder with state attributes."""
        self.messages = messages or []
        self.query = query
        self.temp = temp or {}
        self.plan = plan
        self.last_action = ""
        self.available_actions = ["plan", "api", "alter", "end"]


    def agentic_loop(self):
        """
        This function is used to run the agentic loop. It will select between running kaggle api search, altering the temp dict in the state, or selecting a dataset (END).
        """
        
        while True:
            # only store the last 20 messages
            self.messages = self.messages[-20:]
            tmp_folders = get_file_names("./tmp")

            prompt_inject = {
                "query": self.query,
                # ----- plan related injects -----
                "existing_plan": "Here is your plan: " + self.plan if self.plan != "" else "",
                "next_step_plan" : "- plan: change the long-term plan" if self.last_action != "plan" else "",
                # ----- api related injects -----
                "next_step_api" : "- api: use the kaggle api to search for datasets, download them, or learn about its file structure" if self.last_action != "api" else "",
                "details_api" : "'what to do using the api'" if self.last_action != "api" else "",
                # ----- alter related injects -----
                "next_step_alter" : "- alter: alter the key-values in the temp dict" if self.last_action != "alter" else "",
                "details_alter" : "'key-value pair in format key: value'" if self.last_action != "alter" else "",
               
                "tmp_folder_names": tmp_folders,
                "available_actions": " | ".join( f"'{a}'" for a in self.available_actions if a != self.last_action),
            }

            # run the central message
            central_msg = HumanMessage(content=db_finder_loop_prompt.format(**prompt_inject))

            result_json = chat_invoke(central_msg, self.messages, "json")
        
            # add the messages to the state in a custom way
            self.messages.append(HumanMessage(content="What is your action?"))
            self.messages.append(AIMessage(
                content=f"I chose to {result_json['action']} because {result_json['reason']}"
            ))
            print(f"I chose to {result_json['action']} because {result_json['reason']}")

            # execute the actions
            if result_json['action'] == 'plan':
                self.plan_steps()
            elif result_json['action'] == 'api':
                self.run_kaggle_api(result_json['details'])
            elif result_json['action'] == 'alter':
                self.temp[result_json['details'].split(':')[0]] = result_json['details'].split(':')[1]
                print("temp: " + str(self.temp))
            elif result_json['action'] == 'end':
                return self, result_json['details']
            else:
                # send error to the messages 
                self.messages.append(SystemMessage(content=f"Invalid action. Please try again. Here is the error: {str(e)}"))
                continue
            self.last_action = result_json['action']

    def plan_steps(self):
        """Plans the search for a dataset."""
        
        plan_msg = HumanMessage(content=
            db_finder_plan_search_prompt.format(query=self.query, temp=" ".join([f"{k}: {v}" for k, v in self.temp.items()]))
        )
        result = chat_invoke(plan_msg, self.messages, "str")
        self.plan = result
        self.messages.append(HumanMessage(content="Now that we have a plan, let's proceed with the search?"))

    def run_kaggle_api(self, task):
        """Runs the kaggle api command in the code interpreter."""

        # use LLM to generate kaggle command based on the task
        msg = HumanMessage(content=db_finder_kaggle_api.format(
            task=task,
        ))

        result = chat_invoke(msg, self.messages, "json")
        kaggle_api_command = result['command']
        print("kaggle api command: ", kaggle_api_command)

        # run the kaggle api command
        out, _ = cli_kaggle_docker(kaggle_api_command)

        print("out: ", out)
        # parse the output of the kaggle api command
        out = parse_subprocess_output(out, "backend-kaggle-api")
        print(out)

        # Copy the docker tmp folder to the local tmp folder, in case files are downloaded
        subprocess.run(["docker", "cp", "backend-kaggle-api-1:/tmp/", "./tmp"])

        # store the output in the message history
        if "error" in out.lower():
            self.messages.append(SystemMessage(content="Here is the error. Use this to guide changes to the command: " + out))
        else:
            self.messages.append(SystemMessage(content="Here is the output of the command: " + out))

# TESTING
# agentic_loop(
#     {
#         'messages': [],
#         'query': 'Find me a dataset of house prices in UAE and store it locally in tmp folder',
#         'temp': {},
#         'loop_results': [],
#         'plan': ''
#     }
# ) 