# STORES ALL THE LARGE PROMPTS


## DATABASE FINDER AGENT ------------------------------------------------------------
db_finder_loop_prompt =  """
  Based on the above messages, are you getting closer to {query}?
  You are an efficient helpful assistant that can help with a task of finding a dataset on kaggle and downloading it.
  
  Heres what we have access to:
    tmp directory: {tmp_folder_names}

  Here's the exisitng plan:
  {existing_plan}

  What's the next best step?
    {next_step_plan}
    {next_step_api}
    {next_step_alter}
    - end: completed task (END)

    RETURN IN FOLLOWING FORMAT:
    {{
        "action": {available_actions},
        "details": {details_api} | {details_alter} | "the end notes" | null
        "reason": "reason for the action"
    }}
"""

db_finder_kaggle_api = """
Based on the task ({task}) and the above previous messages, generate the kaggle api command. Here's how to do it.

USAGE OF KAGGLE DATASETS:
usage: kaggle datasets [-h] (list | files | download) ...
options:
  -h, --help            show this help message and exit
commands:
  list                List/search for available datasets
  files               Show dataset files
  download            Download dataset files

HOW TO USE KAGGLE DATASETS LIST:
usage: kaggle datasets list [-h] [--sort-by SORT_BY] [-s SEARCH] [-p PAGE] [-v] [--max-size MAX_SIZE]
options:
  --sort-by SORT_BY     Sort list results. Default is 'hottest'. Valid options are 'hottest', 'votes', 'updated', and 'active'
  -s, --search SEARCH   Term(s) to search for
  -p, --page PAGE       Page number for results paging. Page size is 20 by default
  -v, --csv             Print results in CSV format (if not set print in table format)
  --max-size MAX_SIZE   Specify the maximum size of the dataset to return (bytes)

HOW TO USE KAGGLE DATASETS FILES:
usage: kaggle datasets files [-h] [-v] [--page-size PAGE_SIZE] [dataset]
options:
  dataset               Dataset URL suffix in format <owner>/<dataset-name>
  --page-size PAGE_SIZE Number of items to show on a page. Default size is 20, max is 200

HOW TO USE KAGGLE DATASETS DOWNLOAD:
usage: kaggle datasets download [-h] [-f FILE_NAME] [-p PATH] [--unzip] [dataset]
options:
  -p, --path PATH       Folder where downloaded. Use the tmp folder to store the files.
  --unzip               Unzip the downloaded file. Will delete the zip file when completed.

command examples: 
- kaggle datasets list --search "house prices"
- kaggle datasets files "abhishek/house-prices-advanced-regression-techniques"
- kaggle datasets download "abhishek/house-prices-advanced-regression-techniques" -p tmp/house_prices

YOU MUST RETURN IN THE FOLLOWING FORMAT:
{{
    "command": "kaggle datasets <your_command>"
}}
"""

db_finder_plan_search_prompt = """
        You have access to the following information:
        - the user's query: {query}
        - the temp dict: {temp}

        You also have access to previous messages. Use this space to write your thoughts. Return in plain english and keep it short.
        """


## CODE INTERPRETER AGENT ------------------------------------------------------------
code_inter_loop_prompt = """
      Based on the above messages, are you getting closer to {user_query}?
      Here's what we have access to:
      - files in memory: {keys_of_mem}
      - facts: {kv_pairs_facts}

      Here is your tmp folder:
      {tmp_folder}

      Here's the exisitng plan: {plan}

      What's the next best step?
      {next_step_run}
      {next_step_fact}
      {next_step_plan}
      - end: return final answer or why you can't do this task (END)

      RETURN IN THE FOLLOWING FORMAT:
      {{
          "action": {available_actions},
          "details": {{
              {details_run}
              {details_fact}
              "final_answer": "Answer to return or Why you can't do this task" | null
          }},
          "reason": "Explanation for taking this action"
      }}
  """

code_inter_run_code_prompt = """   
    To access a memory variable, here's the syntax:
    - our_dict = pickle.load(open('{memory_location}', 'rb'))
    - our_dict['variable_name']

    To store a result in memory, here's the syntax:
    - our_dict['variable_name'] = result
    - pickle.dump(our_dict, open('{memory_location}', 'wb'))
    
    Here are the packages you can use: [pandas, numpy, scikit-learn]
    Here are the facts you have: {facts_kv_pairs}
    Here is the tmp folder: 
    {tmp_folder}
    Use the correct path when accessing files in the tmp folder.

    Please write the code to guide you towards the code goal: {code_goal}
    Add print statements in your code. Don't generate fake data.
    RETURN ONLY THE CODE AS A STRING
"""


## MANAGER AGENT ------------------------------------------------------------

manager_stage_one_prompt = """
      You are a helpful manager who controls two assistants.
      The first assistant is a database_finder_agent that is a kaggle api expert.
      The second assistant is a code_interpreter_agent that is a python programmer.
      You will be given a user query. What should our next task be?
      
      user query : {user_query} 
      Use the previous messages.
      Here's what we have done so far: {findings_so_far}

      YOU MUST RESPOND WITH VALID JSON ONLY. DO NOT INCLUDE ANY TEXT OUTSIDE OF THE JSON STRUCTURE.
      
      RETURN IN THE FOLLOWING FORMAT:
      {{
      "assistant": "database_finder_agent" | "code_interpreter_agent" | "END",
      "details": "details of the exact action the assistant needs to take",
      "reason": "reason for choosing the assistant or ending"
      }}                        
      
  """

manager_stage_one_optimized_prompt = """
  You are a helpful manager who controls two assistants (database_finder_agent and code_interpreter_agent).
  user query : {user_query}   
"""

manager_stage_two_prompt = """
  Your task is to audit the work of the manager and grade it ensuring the best possible decision.
  
  grading scale : 1 (worst) to 5 (best).
  chat history : {messages}
  user query : {user_query}
  manager's decision : {manager_decision}
  manager's thinking : {manager_thinking}
                          
  YOU MUST RESPOND WITH VALID JSON ONLY. DO NOT INCLUDE ANY TEXT OUTSIDE OF THE JSON STRUCTURE.
      
  RETURN IN THE FOLLOWING FORMAT:
  {{
  "grade": "1" | "2" | "3" | "4" | "5",
  "reason": "reason for the grade"
  }}                        
"""