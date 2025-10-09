import json
import os
import re
from openai import AzureOpenAI
from PDFer import export_conversation_to_pdf

def talk(deployment_1: str, prompt_1: str, deployment_2: str, prompt_2: str, ignition: str = "", turns: int = 5):
    try:
        api_version, key, endpoint = load_api_config()
    except Exception as e:
        print("Error loading configuration:", e)
    client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=key,
)
    turn = True
    A = [{"role": "system", "content": prompt_1}]
    B = [{"role": "system", "content": prompt_2}]
    ret = [{"role": "setup for A:", "content": prompt_1}, {"role": "setup for B:", "content": prompt_2}]
    if ignition != "":
        A.append({"role": "user", "content": ignition})
        B.append({"role": "assistant", "content": ignition})
        ret.append({"role": "From user to A, impersonating B:", "content": ignition})
        turn = False
    for i in range(turns):
        if turn:
            response = client.chat.completions.create(
                messages=A,
                max_completion_tokens=1000,
                model=deployment_1
            )
            A.append({"role": "assistant", "content": response.choices[0].message.content})
            B.append({"role": "user", "content": response.choices[0].message.content})
            ret.append({"role": "A:", "content": response.choices[0].message.content})
        else:
            response = client.chat.completions.create(
                messages=B,
                max_completion_tokens=10000,
                model=deployment_2
            )
            B.append({"role": "assistant", "content": response.choices[0].message.content})
            A.append({"role": "user", "content": response.choices[0].message.content})
            ret.append({"role": "B:", "content": response.choices[0].message.content}) 
        turn = not turn
    export_conversation_to_pdf(messages=ret)
    return

def load_api_config(config_path="config/setupModels.json"):
    """Load API configuration values from a JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract values
    api_version = data.get("api_version")
    key = data.get("key")
    endpoint = data.get("endpoint")
    
    if not all([api_version, key, endpoint]):
        raise ValueError("Missing one or more required fields in setupModels.json")
    
    return api_version, key, endpoint
