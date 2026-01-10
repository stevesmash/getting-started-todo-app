import requests

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_phone_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    api_key = get_api_key(owner, "NUMVERIFY_API_KEY")
    if not api_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing NUMVERIFY_API_KEY in API vault. Get one at https://numverify.com/",
        }

    phone = entity.name.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    r = requests.get(
        "http://apilayer.net/api/validate",
        params={"access_key": api_key, "number": phone},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()

    if not data.get("valid", False):
        invalid_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name="Invalid Phone Number",
                kind="verification",
                description=f"Phone number {phone} is not valid",
            ),
        )
        nodes.append(invalid_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=invalid_ent.id,
                    relation="verified_as",
                ),
            )
        )
        return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}

    country_name = data.get("country_name", "Unknown")
    country_code = data.get("country_code", "")
    location = data.get("location", "")
    carrier = data.get("carrier", "")
    line_type = data.get("line_type", "")
    international_format = data.get("international_format", phone)

    info_parts = [
        f"Country: {country_name} ({country_code})",
        f"Location: {location}" if location else None,
        f"Carrier: {carrier}" if carrier else None,
        f"Type: {line_type}" if line_type else None,
        f"Format: {international_format}",
    ]
    info_parts = [p for p in info_parts if p]

    verification_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"Phone: Valid ({line_type})",
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

    if country_name and country_name != "Unknown":
        country_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=country_name,
                kind="location",
                description=f"Country code: {country_code}",
            ),
        )
        nodes.append(country_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=country_ent.id,
                    relation="located_in",
                ),
            )
        )

    if carrier:
        carrier_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=carrier,
                kind="organization",
                description=f"Phone carrier for {international_format}",
            ),
        )
        nodes.append(carrier_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=carrier_ent.id,
                    relation="provided_by",
                ),
            )
        )

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
