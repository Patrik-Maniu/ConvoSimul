import json
from pathlib import Path


def talk(msgs, dep, max_tokens):
    from openai import AzureOpenAI

    api_version, key, endpoint = load_api_config()

    with AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=key,
    ) as client:
        response = client.chat.completions.create(
            messages=msgs,
            model=dep,
            max_completion_tokens=max_tokens,
            n=1,
        )

    content = response.choices[0].message.content

    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            "Il modello non ha restituito contenuto testuale."
        )

    return content


def load_api_config(config_path=None):
    path = (
        Path(config_path)
        if config_path is not None
        else Path(__file__).resolve().parent
        / "config"
        / "setupModels.json"
    )

    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    api_version = data.get("api_version")
    key = data.get("key")
    endpoint = data.get("endpoint")

    if not all([api_version, key, endpoint]):
        raise ValueError(
            "Missing one or more required fields in setupModels.json"
        )

    return api_version, key, endpoint
