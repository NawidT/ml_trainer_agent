import os
from langchain_openai.chat_models import ChatOpenAI

chat = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ['OPENAI_API_KEY'])

# handles the planning and eval LLMs
# connects to the database_finder_agent and code_interpreter_agent
# stores the chat_history[list: BaseMessage] and key_facts[dict] 


