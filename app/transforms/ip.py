import requests

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_ip_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    abuse_key = get_api_key(owner, "ABUSEIPDB_API_KEY")

    if not abuse_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing ABUSEIPDB_API_KEY in API vault",
        }

    r = requests.get(
        "https://api.abuseipdb.com/api/v2/check",
        headers={"Key": abuse_key, "Accept": "application/json"},
        params={"ipAddress": entity.name, "maxAgeInDays": 90},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json().get("data", {})

    score = data.get("abuseConfidenceScore", 0)
    country = data.get("countryCode") or "UNK"
    isp = data.get("isp") or "Unknown ISP"

    threat_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"AbuseIPDB score={score}",
            kind="threat",
            description=f"country={country}, isp={isp}",
        ),
    )
    nodes.append(threat_ent)

    rel = store.create_relationship(
        owner=owner,
        payload=RelationshipCreate(
            source_entity_id=entity.id,
            target_entity_id=threat_ent.id,
            relation="reported_as",
        ),
    )
    edges.append(rel)

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
