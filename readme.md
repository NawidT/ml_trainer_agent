
# ML Trainer Agent

An intelligent agent system that helps automate the machine learning workflow - from dataset discovery to model training and evaluation.

## Overview

This project uses a multi-agent system powered by LangGraph and LangChain to:

1. Find relevant datasets on Kaggle based on user queries using natural language
2. Analyze and prepare the data for machine learning tasks
3. Train and evaluate ML models while documenting the process

The system leverages Docker containers for isolation and reproducibility, and uses the Kaggle API to search and download datasets. The agents communicate through a central orchestrator that maintains the conversation state and key facts.

## Project Outline

![Project Outline](https://github.com/NawidT/ml_trainer_agent/blob/main/project_outline.png)


## Key Learnings

There were loads I learnt 

1. Importance of splitting chat sessions per agent and 
2. Power of adding plan to prompt, improving reasoning ability
3. Passing errors back into LLM's help it improve the code, but its coding reasoning is still wack
4. Utilizing Docker to spin up containers, mount files, and copy results back into my file system
5. Learned how to run code within python process (using subprocess) and how to connect it to persistent memory (session based pickle files)
