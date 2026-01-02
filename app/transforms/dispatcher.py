from app.transforms.ip import run_ip_transforms
from app.transforms.domain import run_domain_transforms
from app.transforms.url import run_url_transforms


def run_transforms(entity, owner: str) -> dict:
    kind = (entity.kind or "").lower().strip()

    if kind == "ip":
        return run_ip_transforms(entity, owner)
    if kind == "domain":
        return run_domain_transforms(entity, owner)
    if kind == "url":
        return run_url_transforms(entity, owner)

    return {"nodes": [], "edges": [], "message": f"No transforms for kind='{entity.kind}'"}
