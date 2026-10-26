import json
from pathlib import Path
from request_control import ensure_requests_allowed

def talk(msgs, dep, max_tokens):
    from openai import AzureOpenAI

    api_version, key, endpoint = load_api_config()

    with AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=key,
        max_retries=0,
    ) as client:

        ensure_requests_allowed()

        response = client.chat.completions.create(
            messages=msgs,
            model=dep,
            max_completion_tokens=max_tokens,
            n=1,
        )

    choice = response.choices[0]
    content = choice.message.content

    if not isinstance(content, str) or not content.strip():
        usage = response.usage
        details = getattr(
            usage,
            "completion_tokens_details",
            None,
        )

        raise ValueError(
            "Il modello non ha restituito contenuto testuale. "
            f"deployment={dep}; "
            f"finish_reason={choice.finish_reason}; "
            f"limite={max_tokens}; "
            f"completion_tokens="
            f"{getattr(usage, 'completion_tokens', None)}; "
            f"reasoning_tokens="
            f"{getattr(details, 'reasoning_tokens', None)}; "
            f"refusal={getattr(choice.message, 'refusal', None)!r}"
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
