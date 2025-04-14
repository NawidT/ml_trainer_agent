import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import subprocess
import os
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from utils import parse_subprocess_output, chat_invoke, get_file_names, get_memory_keys
from prompts import code_inter_run_code_prompt, code_inter_loop_prompt

class CodeInterpreter:
    def __init__(self, messages=None, memory_location="tmp/memory.pkl", facts=None, 
                 code_file="tmp/codespace.py", user_query="", plan="", send_frontend_message=None):
        """Initialize the CodeInterpreter with state attributes."""
        self.messages = messages or []
        self.memory_location = memory_location  # stores memory in pickle file, can be accessed by generated subprocess
        self.facts = facts or {}
        self.code_file = code_file
        self.user_query = user_query
        self.plan = plan
        self.code_goal = ""
        self.last_action = ""
        self.available_actions = ["run", "store_fact", "plan", "end"]
        self.send_frontend_message = send_frontend_message

    async def agentic_loop(self):
        """
        This function is used to run the agentic loop of the code interpreter.
        """
        while True:
            # only store the last 20 messages and grab tmp folder file names
            self.messages = self.messages[-20:]
            tmp_folder = get_file_names("./tmp")
    
            prompt_inject = {
                "user_query": self.user_query,
                "keys_of_mem": get_memory_keys(self.memory_location),
                "kv_pairs_facts": ", ".join([f"{k}: {v}" for k, v in self.facts.items()]),
                "available_actions": " | ".join( f"'{a}'" for a in self.available_actions if a != self.last_action),
                # ----- plan related injects -----
                "plan": "Here is the plan: " + self.plan if self.plan != "" else "",
                "next_step_plan" : "- plan: change the long-term plan" if self.last_action != "plan" else "",
                # ----- run related injects -----
                "next_step_run" : "- run: execute Python code or store something in memory" if self.last_action != "run" else "",
                "details_run" : "'code_goal': 'purpose of the code to be executed' | null" if self.last_action != "run" else "",
                # ----- fact related injects -----
                "next_step_fact" : "- store_fact: save a string fact for later reference" if self.last_action != "store_fact" else "",
                "details_fact" : "'fact': 'fact value' return as ONLY string | null" if self.last_action != "store_fact" else "",
                "tmp_folder": tmp_folder
            }

            # run the central message
            central_msg = HumanMessage(content=code_inter_loop_prompt.format(**prompt_inject))
          
            result_json = await chat_invoke(central_msg, self.messages, "json")

            # add the messages to the state in an efficient way
            self.messages.append(HumanMessage(content="What is your action?"))
            self.messages.append(AIMessage(
                content=f"I chose to {result_json['action']} because {result_json['reason']}"
            ))
            print(f"I chose to {result_json['action']} because {result_json['reason']}")
            
            # execute the actions
            if result_json['action'] == 'run':
                self.code_goal = result_json['details']['code_goal']
                await self.run_code(self.code_goal)

            elif result_json['action'] == 'store_fact':
                if result_json['details'] is not None and result_json['details']['fact'] is not None and type(result_json['details']['fact']) == str:
                    await self.store_fact(result_json['details']['fact'])
                else:
                    self.messages.append(SystemMessage(content="Invalid fact. Please try again."))
                    continue

            elif result_json['action'] == 'plan':
                await self.plan_steps()

            elif result_json['action'] == 'end':
                if result_json['details'] is not None and result_json['details']['final_answer'] is not None:
                    return result_json['details']['final_answer']
                else:
                    self.messages.append(SystemMessage(content="Invalid final answer. Please try again."))
                    continue
            self.last_action = result_json['action']
        
    async def plan_steps(self):
        """Plans the search for the kaggle dataset."""

        # use LLM to generate a plan for the search
        msg = HumanMessage(content="Based on the above messages, use this space to write a short plan for your thoughts to proceed with the next steps.")
        result = await chat_invoke(msg, self.messages, "str")
        # add the plan to the state and it will be used in future loop messages until plan changes
        self.plan = result
        await self.send_frontend_message("python_agent", "text", f"Plan: {result}")
    
    
    async def run_code(self, code_goal):
        """Runs the code in the code interpreter and potentially stores the result in memory."""

        # pass the code thru another LLM with more detailed information and request changes
        tmp_folder = get_file_names("./tmp")
        more_info_msg = HumanMessage(content=code_inter_run_code_prompt.format(
            facts_kv_pairs= ", ".join([f"{k}: {v}" for k, v in self.facts.items()]),
            code_goal=code_goal,
            memory_location=self.memory_location,
            tmp_folder=tmp_folder
        ))
        
        generated_code = await chat_invoke(more_info_msg, self.messages, "str")
        self.messages.append(AIMessage(content=generated_code))

        if generated_code.startswith("```python"):
            generated_code = generated_code.replace("```python", "", 1)
        if generated_code.endswith("```"):
            generated_code = generated_code.rsplit("```", 1)[0]

        print(generated_code)
        await self.send_frontend_message("python_agent", "python", generated_code)

        # save the code in a python file (codespace.py)
        with open(self.code_file, 'w') as f:
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
            await self.send_frontend_message("python_agent", "cli", out)
        except Exception as e:
            print(e)
            self.messages.append(SystemMessage(content="Error running code. Please try again. " + str(e)))
            return
        # grab the output/findings of the code and store in message history
        self.messages.append(SystemMessage(content="Here is the output of the code: " + out))

    async def store_fact(self, fact):
        """Stores the fact in the state."""

        # rewrite the fact string as a key:value pair
        msg = HumanMessage(content=f"""
            Using the following information, convert the fact into a key:value pair. 
            fact: {fact}.
            Make sure the key is unique. Here are the existing keys: {self.facts.keys()}.
            RETURN ONLY THE KEY:VALUE PAIR AS A STRING
        """)

        kv_pair = await chat_invoke(msg, self.messages, "str")
        print(kv_pair)

        # add the fact to the state
        self.facts[kv_pair.split(':')[0]] = kv_pair.split(':')[1]

        # show all the facts
        print(self.facts)
        await self.send_frontend_message("python_agent", "text", f"StoredFacts: {self.facts}")
# TESTING
# agentic_loop(
#     {
#         'messages': [],
#         'code': '',
#         'user_query': '''On the exisiting dataset, find me the top 10 most expensive properties in UAE''',
#         'facts': {},
#         'memory_location': 'tmp/memory.pkl', # use relative path since both in same directory (tmp)
#         'code_file': 'tmp/codespace.py',
#         'plan': ''
#     }
# )