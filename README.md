# ConvoSimul

A small GUI app (Python) where **two LLMs talk to each other**
The app then orchestrates the conversation (via Azure OpenAI)

## Features
- User chooses:
  - How to name the 2 LLMs in the conversation
  - 2 models to be used
  - A "system" prompt that will instructs the LLMs on how to interact with each other
  - An optional seed (unfortunatelly it does not guarantee deterministic behaviour)
  - Max tokens per response used by each LLM
  - Number of turns the conversation will go on for
  - File name of where to save data
- These config settings can be saved with a dedicated button
- Saving will create a file named <file name>.json in the directory .\presets
- Presets files can be loaded with a dedicated button
- Once the start button is pressed, a new window will be open where each message will be shown 1 at the time
- In this new window there are 2 buttons
  - Next: will continue the conversation, sending an API request to get the next message completion
  - Stop: will terminate the program and save the conversation and it's configuration in a file named <file name>.pdf in the directory .\outputs
  - Save: will save current conversation in a file named <file name><number of saved in this session>.pdf in the directory .\outputs

## TODOs
- Save conversations as .json too, to be later used as checkpoints
- Load preset conversations
- Get a third LLM to check if the 2 LLMs conversin are going out of scope
- Use files (.pdf, .png etc...) as part of the starting input
- Localization
- Check for max lenth of "system" prompt
- Auto mode for X number of turns (maybe stop if the 3rd LLM deems it necesary)
- Add more LLMs talking to each other
- Handle talking turn if there are more than just 2 LLMs


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
