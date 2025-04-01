
# ML Trainer Agent

An intelligent agent system that helps automate the machine learning workflow - from dataset discovery to model training and evaluation.

## Overview

This project uses a multi-agent system powered by LangGraph and LangChain to:

1. Find relevant datasets on Kaggle based on user queries using natural language
2. Analyze and prepare the data for machine learning tasks
3. Train and evaluate ML models while documenting the process

The system leverages Docker containers for isolation and reproducibility, and uses the Kaggle API to search and download datasets. The agents communicate through a central orchestrator that maintains the conversation state and key facts.

Essentially we have:
- Manager Agent : in charge of distributing and overlooking progress. Handles passing tasks from one agent to another
- Kaggle Agent : expert in Kaggle API, handles finding datasets and downloading them
- Coding Agent : expert in Python, runs code in a dockerized env using a step-by-step approach (runs code, sees output, changes code, run again)

## Project Outline

![Project Outline](https://github.com/NawidT/ml_trainer_agent/blob/main/backend/project_outline.png)


## Key Learnings

There were loads I learnt 

1. Importance of splitting chat sessions per agent and message chains to be optimized to only include chat-change info rather than informational jargon e.g. how kaggle api works
2. Power of adding plan to prompt, improving reasoning ability
3. Passing errors back into LLM's help it improve the code, but its coding reasoning is still wack
4. Utilizing Docker to spin up containers, mount files, and copy results back into my file system
5. Learned how to run code within python process (using subprocess) and how to connect it to persistent memory (session based pickle files)

## Future Things to Work On

- Concurrent working agents : Using the current architecture, the agents essentially work in one workflow. But some tasks can be pre-done while one agent is doing something. For instance, if our user wants to use a UAE-real-estate ML model to predict California house prices, while python agent trains on UAE data, the kaggle agent can fetch California data
- RL capabilities : since in the main loop, we have a grading mechanism to see how well the manager is performing, we can utilize the grades + actions_so_far to create an RL based learnings. The only question is, where can we apply our RL learnings within an agent? 
- Adding guard rails: centralized guardrails system
