# ConvoSimul

A small GUI app (Python) where **two LLMs talk to each other**
The app then orchestrates the conversation (via Azure OpenAI)

## Features
- User chooses:
  - What language the UI is in
  - How to name the 2 LLMs in the conversation
  - 2 models to be used
  - A "system" prompt that will instructs the LLMs on how to interact with each other
  - An optional seed (unfortunatelly it does not guarantee deterministic behaviour)
  - Max tokens per response used by each LLM
  - A color for each model, represented in a hex value
  - Number of turns the conversation goes on for before stopping
  - If a referee watches the conversation and stops it if ti goes out of context
  - File name of where to save data
- Be able to load a custom conversation as a start
- These config settings can be saved with a dedicated button
- Saving will create a file named <file name>.json in the directory .\presets
- Presets files can be loaded with a dedicated button
- Once the start button is pressed, a new window will be open where messages will be loaded depending on the number of turns selected
- In this new window there are 3 buttons and a text form
  - Turns: How many turns to do before next stop, if empty or NaN it will do just 1 turn
  - Next: will continue the conversation for the number of turns selected, sending an API request to get the next message completion
  - Stop: will terminate the program and save the conversation and it's configuration in a file named <file name>.pdf in the directory .\outputs
  - Save to PDF: will save current conversation in a file named <file name><number of saved in this session>.pdf in the directory .\outputs
  - Save to JSON: will save current conversation in a file named <file name><number of saved in this session>.json in the directory .\conversations

## TODOs
- FIX: importing conversations will not make the messages colored with the right colors
- Use files (.pdf, .png etc...) as part of the starting input
- Fix program not responding while waiting for API responce
- Reduce technical debt
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
