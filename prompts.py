# STORES ALL THE LARGE PROMPTS

db_finder_loop_prompt =  """
    You are a helpful assistant that can help with a task of finding a dataset of kaggle based on the user's query {query}. 
    {plan_once}. Be optimal and efficient. 

    You can do the following actions:
    - plan: plan the search for a dataset
    - search: use the kaggle api to narrow the search for a dataset
    - alter: alter the key-values in the temp dict
    - end: select a dataset (END)

    Here is the info of the temp dict:
    {temp}

    {loop_stuck}

    RETURN IN FOLLOWING FORMAT:
    {{
        "action": "plan" | "search" | "alter" | "end",
        "details": "new query to search for" | "key-value pair in format key: value" | "plan for the search" | "the selected dataset's reference"
        "reason": "reason for the action"
    }}
            """

kaggle_api_search_prompt = """ 
        You are a helpful assistant that creates kaggle api search commands. Search the Kaggle API for datasets to get the most relevant results for the user's query: {query}. 
        Use previous messages to direct your search, make sure not to re-search the same thing, be optimal. Do not make bash commands, just return the command as a string.

        Here is the usage for the "kaggle datasets list" command:
        usage: kaggle datasets list [-h] [--sort-by SORT_BY] [--size SIZE] [--file-type FILE_TYPE] [-s SEARCH] [--max-size MAX_SIZE]

        --sort-by SORT_BY     Sort list results. Valid options are 'hottest', 'votes', 'updated', and 'active'
        --size SIZE           DEPRECATED. Please use --max-size and --min-size to filter dataset sizes.
        --file-type FILE_TYPE Search for datasets with a specific file type. Default is 'all'. Valid options are 'all', 'csv', 'sqlite', 'json', and 'bigQuery'. Please note that bigQuery datasets cannot be downloaded
        -s SEARCH, --search SEARCH Term(s) to search for
        --max-size MAX_SIZE   Specify the maximum size of the dataset to return (bytes)

        An example command is:
                kaggle datasets list --sort-by 'hottest' --search 'diabetes'

        YOU MUST RETURN IN THE FOLLOWING FORMAT: 
                kaggle datasets list <your_command>
        """

db_finder_plan_search_prompt = """
        You have access to the following information:
        - the user's query: {query}
        - the temp dict: {temp}

        You also have access to previous messages. Use this space to write your thoughts. Return in plain english.
        """