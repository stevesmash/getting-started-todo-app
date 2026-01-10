import requests

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_whois_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    api_key = get_api_key(owner, "WHOISXML_API_KEY")
    if not api_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing WHOISXML_API_KEY in API vault. Get one at https://whois.whoisxmlapi.com/",
        }

    domain = entity.name.strip()

    r = requests.get(
        "https://www.whoisxmlapi.com/whoisserver/WhoisService",
        params={
            "apiKey": api_key,
            "domainName": domain,
            "outputFormat": "JSON",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json().get("WhoisRecord", {})

    registrar_name = data.get("registrarName", "Unknown")
    creation_date = data.get("createdDate", "")
    expiry_date = data.get("expiresDate", "")
    updated_date = data.get("updatedDate", "")
    status = data.get("status", "")

    registrant = data.get("registrant", {})
    registrant_name = registrant.get("name", registrant.get("organization", ""))
    registrant_country = registrant.get("country", "")
    registrant_email = registrant.get("email", "")

    name_servers = data.get("nameServers", {}).get("hostNames", [])

    info_parts = [
        f"Registrar: {registrar_name}",
        f"Created: {creation_date[:10]}" if creation_date else None,
        f"Expires: {expiry_date[:10]}" if expiry_date else None,
        f"Updated: {updated_date[:10]}" if updated_date else None,
    ]
    info_parts = [p for p in info_parts if p]

    whois_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"WHOIS: {registrar_name}",
            kind="whois",
            description=", ".join(info_parts),
        ),
    )
    nodes.append(whois_ent)
    edges.append(
        store.create_relationship(
            owner=owner,
            payload=RelationshipCreate(
                source_entity_id=entity.id,
                target_entity_id=whois_ent.id,
                relation="registered_with",
            ),
        )
    )

    if registrant_name:
        registrant_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=registrant_name,
                kind="person" if not registrant.get("organization") else "organization",
                description=f"Country: {registrant_country}" if registrant_country else "",
            ),
        )
        nodes.append(registrant_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=registrant_ent.id,
                    relation="registered_by",
                ),
            )
        )

    if registrant_email and "@" in registrant_email and "privacy" not in registrant_email.lower():
        email_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=registrant_email,
                kind="email",
                description=f"Registrant email for {domain}",
            ),
        )
        nodes.append(email_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=email_ent.id,
                    relation="contact_email",
                ),
            )
        )

    for ns in name_servers[:3]:
        ns_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=ns,
                kind="nameserver",
                description=f"Name server for {domain}",
            ),
        )
        nodes.append(ns_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=ns_ent.id,
                    relation="uses_nameserver",
                ),
            )
        )

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
