import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from agents.db_finder import agentic_loop as db_finder_agentic_loop, DBFinderState
from agents.code_interpreter import agentic_loop as code_inter_agentic_loop, CodeInterpreterState
from utils import chat_invoke
from prompts import manager_stage_one_prompt, manager_stage_one_optimized_prompt, manager_stage_two_prompt
class MainState(TypedDict):
    messages: list[BaseMessage]
    user_query: str

# refresh the memory.pkl file``
def refresh_memory():
    if os.path.exists("tmp/memory.pkl"):
        os.remove("tmp/memory.pkl")
    
    # create a new memory.pkl file
    with open("tmp/memory.pkl", "w") as f:
        pass

def main(state: MainState):
    """
    This function is used to run the main loop.
    """
    refresh_memory()
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

    while True:
        # used to store manager's thoughts until a decision is made
        mini_chain = []

        # initiate stage one; manager agent makes initial decision
        stage_one_msg = HumanMessage(content=manager_stage_one_prompt.format(user_query=state['user_query']))
        stage_one_json = chat_invoke(stage_one_msg, state['messages'], "json", "main")

        # store optimized messages of Human-AI interaction
        mini_chain.append(HumanMessage(content=manager_stage_one_optimized_prompt.format(user_query=state['user_query'])))
        mini_chain.append(AIMessage(
            content="I chose the " + stage_one_json['assistant'] + " because " + stage_one_json['reason']
        ))
        print("manager chose : " + stage_one_json['assistant'] + " because " + stage_one_json['reason'])

        # initiate stage two; self-audit the work of the manager and grade your work
        stage_two_msg = HumanMessage(content=manager_stage_two_prompt.format(
            messages=state['messages'][-20:], user_query=state['user_query'], 
            manager_decision=stage_one_json['assistant'] + " -> " + stage_one_json['reason'],
            manager_thinking=mini_chain
        ))

        stage_two_json = chat_invoke([stage_two_msg], "json", "main")
        grade = int(stage_two_json['grade'])
        print("self grade : " + str(grade) + " because " + stage_two_json['reason'])
        
        # if the grade is less than 2, the manager made a bad decision
        # for bad decisions, we will restart the loop and not append messages to the chain
        # for good decisions, we will continue the loop and append messages to the chain
        if grade < 2:
            mini_chain.append(AIMessage(content="I made a bad decision. Please try again."))
            continue
        else:
            mini_chain = [] # reset the mini_chain
            # finally append the decision to the chain
            state["messages"].append(HumanMessage(content=manager_stage_one_optimized_prompt.format(user_query=state['user_query'])))
            state['messages'].append(AIMessage(
                content=f"I made a good decision. I chose the {stage_one_json['assistant']} because {stage_one_json['reason']}"
            ))

            
            print("-----------------------------------" + stage_one_json['assistant'] + "-----------------------------------")
            if stage_one_json['assistant'] == "database_finder_agent":
                db_finder_state['query'] = stage_one_json['details']
                db_finder_state['plan'] = ""
                db_finder_state, findings = db_finder_agentic_loop(db_finder_state)
                print("db_finder_state : " + findings)
                state['messages'].append(HumanMessage(content="Here are the findings from the database_finder_agent: " + findings))
            elif stage_one_json['assistant'] == "code_interpreter_agent":
                code_inter_state['user_query'] = stage_one_json['details']
                code_inter_state, findings = code_inter_agentic_loop(code_inter_state)
                print("code_inter_state : " + findings)
                state['messages'].append(HumanMessage(content="Here are the findings from the code_interpreter_agent: " + findings))
            elif stage_one_json['assistant'] == "END":
                print("ENDING REASON : " + stage_one_json['reason'])
                return stage_one_json['reason']


main(
    {
        'messages': [],
        'user_query': """
            Find me a dataset of house prices in UAE and store it locally in tmp folder. 
            Create a predictive model for house prices in UAE. 
            Then find houses in California with the same features and predict their prices. 
            Report the accuracy of the UAE-based model on California-based data.
        """
    }
)