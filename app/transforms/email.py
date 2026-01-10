import requests

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_email_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    api_key = get_api_key(owner, "HUNTER_API_KEY")
    if not api_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing HUNTER_API_KEY in API vault. Get one at https://hunter.io/api",
        }

    r = requests.get(
        "https://api.hunter.io/v2/email-verifier",
        params={"email": entity.name, "api_key": api_key},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json().get("data", {})

    status = data.get("status", "unknown")
    score = data.get("score", 0)
    disposable = data.get("disposable", False)
    webmail = data.get("webmail", False)
    mx_records = data.get("mx_records", False)
    smtp_server = data.get("smtp_server", {})
    sources = data.get("sources", [])

    info_parts = [
        f"Status: {status}",
        f"Score: {score}",
        f"Disposable: {disposable}",
        f"Webmail: {webmail}",
        f"MX Records: {mx_records}",
    ]

    verification_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"Email Verification: {status}",
            kind="verification",
            description=", ".join(info_parts),
        ),
    )
    nodes.append(verification_ent)
    edges.append(
        store.create_relationship(
            owner=owner,
            payload=RelationshipCreate(
                source_entity_id=entity.id,
                target_entity_id=verification_ent.id,
                relation="verified_as",
            ),
        )
    )

    domain = entity.name.split("@")[-1] if "@" in entity.name else None
    if domain:
        domain_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=domain,
                kind="domain",
                description=f"Email domain from {entity.name}",
            ),
        )
        nodes.append(domain_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=domain_ent.id,
                    relation="belongs_to",
                ),
            )
        )

    for source in sources[:5]:
        source_domain = source.get("domain", "")
        if source_domain:
            source_ent = store.create_entity(
                owner=owner,
                payload=EntityCreate(
                    case_id=entity.case_id,
                    name=source_domain,
                    kind="source",
                    description=f"Found on: {source.get('uri', 'N/A')}",
                ),
            )
            nodes.append(source_ent)
            edges.append(
                store.create_relationship(
                    owner=owner,
                    payload=RelationshipCreate(
                        source_entity_id=entity.id,
                        target_entity_id=source_ent.id,
                        relation="found_on",
                    ),
                )
            )

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
