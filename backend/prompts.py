# STORES ALL THE LARGE PROMPTS

db_finder_loop_prompt =  """
    You are a helpful assistant that can help with a task of finding a dataset on kaggle and downloading it .
    Here's the user's query {query}. {plan_once}. Be optimal and efficient. 

    You can do the following actions:
    - plan: a space to write your thoughts/plan-of-action
    - api: use the kaggle api to search for datasets, download them, or learn about its file structure
    - alter: alter the key-values in the temp dict
    - end: completed task (END)

    Here's what your tmp folder looks like:
    {tmp_folder}

    Here is the info of the temp dict:
    {temp}

    {loop_stuck}

    RETURN IN FOLLOWING FORMAT:
    {{
        "action": "plan" | "api" | "alter" | "end",
        "details": "what to do using the api" | "key-value pair in format key: value" | "the end notes"
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

YOU MUST RETURN IN THE FOLLOWING FORMAT:
{{
    "command": "kaggle datasets <your_command>"
}}
"""

# kaggle_api_search_prompt = """ 
#         You are a helpful assistant that creates kaggle api search commands. Search the Kaggle API for datasets to get the most relevant results for the user's query: {query}. 
#         Use previous messages to direct your search, make sure not to re-search the same thing, be optimal. Do not make bash commands, just return the command as a string.

#         Here is the usage for the "kaggle datasets list" command:
#         usage: kaggle datasets list [-h] [--sort-by SORT_BY] [--size SIZE] [--file-type FILE_TYPE] [-s SEARCH] [--max-size MAX_SIZE]

#         --sort-by SORT_BY     Sort list results. Valid options are 'hottest', 'votes', 'updated', and 'active'
#         --size SIZE           DEPRECATED. Please use --max-size and --min-size to filter dataset sizes.
#         --file-type FILE_TYPE Search for datasets with a specific file type. Default is 'all'. Valid options are 'all', 'csv', 'sqlite', 'json', and 'bigQuery'. Please note that bigQuery datasets cannot be downloaded
#         -s SEARCH, --search SEARCH Term(s) to search for
#         --max-size MAX_SIZE   Specify the maximum size of the dataset to return (bytes)

#         An example command is:
#                 kaggle datasets list --sort-by 'hottest' --search 'diabetes'

#         YOU MUST RETURN IN THE FOLLOWING FORMAT:
#         {{
#             "command": "kaggle datasets list <your_command>"
#         }}
#         """

db_finder_plan_search_prompt = """
        You have access to the following information:
        - the user's query: {query}
        - the temp dict: {temp}

        You also have access to previous messages. Use this space to write your thoughts. Return in plain english and keep it short.
        """

code_inter_init_prompt = """
            You are an assistant that helps your user get closer to {user_query}
            You have access to the following information:
            - memory: {keys_of_mem} (for storing and accessing Python objects)
            - facts: {kv_pairs_facts} (for storing string-based information)
            - previous messages above

            {plan}

            You can perform the following actions:
            - run: execute Python code or store something in memory
            - store_fact: save a string fact for later reference
            - plan: plan your thoughts
            - end: return final answer or why you can't do this task (END)

            RETURN IN THE FOLLOWING FORMAT:
            {{
                "action": "run" | "store_fact" | "plan" | "end",
                "details": {{
                    "code_goal": "Code goal to guide you towards" | null,
                    "fact": "fact to be stored and it's unique key" | null,
                    "final_answer": "Answer to return" | null
                }},
                "reason": "Explanation for taking this action"
            }}
        """

code_inter_loop_prompt = """
            Based on the above results, are you getting closer to {user_query}?
            You also have access to the following information:
            - memory: {keys_of_mem}
            - facts: {kv_pairs_facts}

            Here is your tmp folder:
            {tmp_folder}

            {plan}
            What's the next best step?

            RETURN IN THE FOLLOWING FORMAT:
            {{
                "action": "run" | "store_fact" | "plan" | "end",
                "details": {{
                    "code_goal": "Code goal to guide you towards" | null,
                    "fact": "fact to be stored and it's unique key" | null,
                    "final_answer": "Answer to return or Why you can't do this task" | null
                }},
                "reason": "Explanation for taking this action"
            }}
        """

code_inter_run_code = """   
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