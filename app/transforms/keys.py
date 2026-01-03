from app.storage import store


def get_api_key(owner: str, name: str) -> str | None:
    keys = store.list_api_keys(owner=owner)
    for k in keys:
        if k.active and (k.name or "").strip().upper() == name.strip().upper():
            return k.description
    return None
