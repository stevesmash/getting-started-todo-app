import requests

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_shodan_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    api_key = get_api_key(owner, "SHODAN_API_KEY")
    if not api_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing SHODAN_API_KEY in API vault. Get one at https://shodan.io/",
        }

    ip = entity.name.strip()

    r = requests.get(
        f"https://api.shodan.io/shodan/host/{ip}",
        params={"key": api_key},
        timeout=30,
    )

    if r.status_code == 404:
        not_found_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name="Shodan: No data",
                kind="analysis",
                description=f"IP {ip} not found in Shodan database",
            ),
        )
        nodes.append(not_found_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=not_found_ent.id,
                    relation="scanned_by",
                ),
            )
        )
        return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}

    r.raise_for_status()
    data = r.json()

    org = data.get("org", "Unknown")
    asn = data.get("asn", "")
    isp = data.get("isp", "")
    country = data.get("country_name", "")
    city = data.get("city", "")
    os = data.get("os", "")
    ports = data.get("ports", [])
    hostnames = data.get("hostnames", [])
    vulns = data.get("vulns", [])

    info_parts = [
        f"Org: {org}",
        f"ASN: {asn}" if asn else None,
        f"ISP: {isp}" if isp else None,
        f"Location: {city}, {country}" if city else f"Country: {country}" if country else None,
        f"OS: {os}" if os else None,
        f"Open ports: {len(ports)}",
    ]
    info_parts = [p for p in info_parts if p]

    scan_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"Shodan: {org}",
            kind="analysis",
            description=", ".join(info_parts),
        ),
    )
    nodes.append(scan_ent)
    edges.append(
        store.create_relationship(
            owner=owner,
            payload=RelationshipCreate(
                source_entity_id=entity.id,
                target_entity_id=scan_ent.id,
                relation="scanned_by",
            ),
        )
    )

    for port in ports[:10]:
        port_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=f"Port {port}",
                kind="port",
                description=f"Open port on {ip}",
            ),
        )
        nodes.append(port_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=port_ent.id,
                    relation="exposes",
                ),
            )
        )

    for hostname in hostnames[:5]:
        hostname_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=hostname,
                kind="domain",
                description=f"Hostname for {ip}",
            ),
        )
        nodes.append(hostname_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=hostname_ent.id,
                    relation="has_hostname",
                ),
            )
        )

    for vuln in vulns[:5]:
        vuln_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=vuln,
                kind="vulnerability",
                description=f"CVE detected on {ip}",
            ),
        )
        nodes.append(vuln_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=vuln_ent.id,
                    relation="vulnerable_to",
                ),
            )
        )

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
