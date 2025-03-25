# STORES ALL THE LARGE PROMPTS

db_finder_loop_prompt =  """
    You are a helpful assistant that can help with a task of finding a dataset of kaggle based on the user's query {query}. 
    {"Be sure to plan your approach only once" if len(state['messages']) == 0 else ""}. Be optimal and efficient. 

    You can do the following actions:
    - plan: plan the search for a dataset
    - search: use the kaggle api to narrow the search for a dataset
    - alter: alter the key-values in the temp dict
    - end: select a dataset (END)

    Here is the info of the temp dict:
    {temp}

    RETURN IN FOLLOWING FORMAT:
    {{
        "action": "plan" | "search" | "alter" | "end",
        "details": "new query to search for" | "new key-value pair" | "plan for the search" | "the selected dataset's reference"
        "reason": "reason for the action"
    }}
            """

kaggle_api_search_prompt = """ 
        You are a helpful assistant that creates kaggle api search commands. Search the Kaggle API for datasets to get the most relevant results for the user's query: {query}. 
        Use previous messages to direct your search, make sure not to re-search the same thing, be optimal. Do not make bash commands, just return the command as a string.

        Here is the usage for the "kaggle datasets list" command:
        usage: kaggle datasets list [-h] [--sort-by SORT_BY] [--size SIZE] [--file-type FILE_TYPE] [--license LICENSE_NAME]
                            [--tags TAG_IDS] [-s SEARCH] [-m] [--user USER] [-p PAGE] [-v] [--max-size MAX_SIZE]
                            [--min-size MIN_SIZE]
        optional arguments:
        -h, --help            show this help message and exit
        --sort-by SORT_BY     Sort list results. Default is 'hottest'. Valid options are 'hottest', 'votes', 'updated', and 'active'
        --size SIZE           DEPRECATED. Please use --max-size and --min-size to filter dataset sizes.
        --file-type FILE_TYPE
                                Search for datasets with a specific file type. Default is 'all'. Valid options are 'all', 'csv', 'sqlite', 'json', and 'bigQuery'. Please note that bigQuery datasets cannot be downloaded
        --license LICENSE_NAME
                                Search for datasets with a specific license. Default is 'all'. Valid options are 'all', 'cc', 'gpl', 'odb', and 'other'
        --tags TAG_IDS        Search for datasets that have specific tags. Tag list should be comma separated
        -s SEARCH, --search SEARCH
                                Term(s) to search for
        -m, --mine            Display only my items
        --user USER           Find public datasets owned by a specific user or organization
        -p PAGE, --page PAGE  Page number for results paging. Page size is 20 by default
        -v, --csv             Print results in CSV format (if not set print in table format)
        --max-size MAX_SIZE   Specify the maximum size of the dataset to return (bytes)
        --min-size MIN_SIZE   Specify the minimum size of the dataset to return (bytes)


        YOU MUST RETURN AS STRING FORMAT: 
        kaggle datasets list <your_command>
        """

db_finder_plan_search_prompt = """
        You are a helpful assistant that plans the search for a dataset. You have access to the following information:
        - the user's query: {query}
        - the temp dict: {temp}

        You also have access to previous messages. You must return a short plan for the search. Return in plain english.
        """