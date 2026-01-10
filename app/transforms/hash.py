import requests

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_hash_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    api_key = get_api_key(owner, "VIRUSTOTAL_API_KEY")
    if not api_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing VIRUSTOTAL_API_KEY in API vault. Get one at https://www.virustotal.com/gui/my-apikey",
        }

    file_hash = entity.name.strip()

    r = requests.get(
        f"https://www.virustotal.com/api/v3/files/{file_hash}",
        headers={"x-apikey": api_key},
        timeout=30,
    )

    if r.status_code == 404:
        unknown_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name="Hash Not Found",
                kind="analysis",
                description=f"Hash {file_hash} not found in VirusTotal database",
            ),
        )
        nodes.append(unknown_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=unknown_ent.id,
                    relation="analyzed_as",
                ),
            )
        )
        return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}

    r.raise_for_status()
    data = r.json().get("data", {})
    attributes = data.get("attributes", {})

    stats = attributes.get("last_analysis_stats", {})
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    harmless = stats.get("harmless", 0)
    undetected = stats.get("undetected", 0)

    file_type = attributes.get("type_description", "Unknown")
    file_size = attributes.get("size", 0)
    file_names = attributes.get("names", [])[:3]

    threat_label = "clean"
    if malicious > 0:
        threat_label = "malicious"
    elif suspicious > 0:
        threat_label = "suspicious"

    analysis_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"VirusTotal: {threat_label}",
            kind="threat" if malicious > 0 else "analysis",
            description=f"Malicious: {malicious}, Suspicious: {suspicious}, Harmless: {harmless}, Undetected: {undetected}",
        ),
    )
    nodes.append(analysis_ent)
    edges.append(
        store.create_relationship(
            owner=owner,
            payload=RelationshipCreate(
                source_entity_id=entity.id,
                target_entity_id=analysis_ent.id,
                relation="analyzed_as",
            ),
        )
    )

    if file_type != "Unknown":
        type_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=f"File Type: {file_type}",
                kind="metadata",
                description=f"Size: {file_size} bytes",
            ),
        )
        nodes.append(type_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=type_ent.id,
                    relation="has_metadata",
                ),
            )
        )

    for fname in file_names:
        name_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=fname,
                kind="filename",
                description=f"Known filename for hash {file_hash[:16]}...",
            ),
        )
        nodes.append(name_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=name_ent.id,
                    relation="known_as",
                ),
            )
        )

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
