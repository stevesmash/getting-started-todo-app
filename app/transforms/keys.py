from typing import Optional
from app.storage import store


def get_api_key(owner: str, key_name: str) -> Optional[str]:
    """Retrieve an API key value from the user's API keys vault by name."""
    try:
        api_keys = store.list_api_keys(owner)
        for key in api_keys:
            if key.name == key_name and key.active:
                return key.key
        return None
    except Exception:
        return None
