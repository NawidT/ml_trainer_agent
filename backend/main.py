import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_openai.chat_models import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from agents.db_finder import agentic_loop as db_finder_agentic_loop, DBFinderState
from agents.code_interpreter import agentic_loop as code_inter_agentic_loop, CodeInterpreterState
from utils import chat_invoke

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
        stage_one_msg = HumanMessage(content="""
            You are a helpful manager who controls two assistants.
            The first assistant is a database_finder_agent that is a kaggle api expert.
            The second assistant is a code_interpreter_agent that is a python programmer.
            You will be given a user query.
            
            user query : {user_query} 
            Use the previous messages.                  

            RETURN IN THE FOLLOWING FORMAT:
            {{
            "assistant": "database_finder_agent" | "code_interpreter_agent" | "END",
            "details": "details of the exact action the assistant needs to take"
            "reason": "reason for choosing the assistant or ending"
            }}                        
            
        """.format(user_query=state['user_query']))

        state['messages'].append(stage_one_msg)
        stage_one_json = chat_invoke(state['messages'], "json", "main")


        stage_two_msg = HumanMessage(content="""
            Your task is to audit the work of the manager and grade its work to make sure it made the best possible decision.
            
            grading scale : 1 being the worst and 5 being the best.
            chat history : {messages}
            user query : {user_query}
            manager's decision : {manager_decision}
                                    
            RETURN IN THE FOLLOWING FORMAT:
            {{
            "grade": "1" | "2" | "3" | "4" | "5",
            "reason": "reason for the grade"
            }}                        
        """.format(
            messages=state['messages'][-20:], user_query=state['user_query'], 
            manager_decision=stage_one_json['assistant'] + " -> " + stage_one_json['reason']
        ))

        stage_two_json = chat_invoke([stage_two_msg], "json", "main")
        grade = int(stage_two_json['grade'])
        print("grade : " + str(grade))

        if grade < 2:
            state['messages'].append(SystemMessage(content="The manager made a bad decision. Please try again."))
            continue
        else:
            state['messages'].append(SystemMessage(content=f"The manager made a good decision. {stage_one_json['details']}"))
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
                print(" ENDING REASON : " + stage_one_json['reason'])
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