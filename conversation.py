import json
import os
from openai import AzureOpenAI

def talk(deployment: str, prompt: str):
    print(f"Starting conversation with deployment '{deployment}' and prompt:\n{prompt}")
    try:
        api_version, key, endpoint = load_api_config()
        print("API Version:", api_version)
        print("Key:", key)
        print("Endpoint:", endpoint)
    except Exception as e:
        print("Error loading configuration:", e)
    client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=key,
)
    response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": prompt,
        }
    ],
    max_completion_tokens=100000,
    model=deployment
)
    print("Response:", response.choices[0].message.content)
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
