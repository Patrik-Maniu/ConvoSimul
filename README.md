# ConvoSimul

A small GUI app (Python) where **two LLMs talk to each other**. The user picks:
- Which **LLM model** powers **Speaker A** (first talker) and **Speaker B** (responder),
- A **starting prompt** for each,
- **Stop conditions**: either a **max number of turns** or when a **trigger substring** appears.

The app then orchestrates the conversation (via Azure OpenAI), and when the stop condition hits, it **saves the full transcript to a text file**.

## Features

- GUI startup: choose model for Speaker A and B, set the initial prompts.
- Turn-taking: A speaks first, B responds, repeat.
- Stop conditions:
  - Max number of responses.
  - Trigger substring detection in any response.
- Exports the full conversation to a .pdf named after the current time of hte conversation

# Setup

complete the setupModels.json in the config folder

## Without virtual enviroment 

```bash

pip install --upgrade pip
pip install openai PyQt6 reportlab
```

## With virtual enviroment
```bash
python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install openai PyQt6 reportlab
```
