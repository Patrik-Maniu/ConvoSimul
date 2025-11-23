import json
import os
import re
from openai import AzureOpenAI

def talk(msgs, dep, seed, max_tokens):
    try:
        api_version, key, endpoint = load_api_config()
    except Exception as e:
        print("Error loading configuration:", e)
    client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=key,
)
    response = client.chat.completions.create(
        messages=msgs,
        model=dep,
        max_completion_tokens=max_tokens,
        n=1,
        seed=seed,
        )
    return response.choices[0].message.content

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
