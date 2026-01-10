import time
import requests
from urllib.parse import urlparse

from app.schemas import EntityCreate, RelationshipCreate
from app.storage import store
from app.transforms.keys import get_api_key


def run_url_transforms(entity, owner: str) -> dict:
    nodes = []
    edges = []

    api_key = get_api_key(owner, "URLSCAN_API_KEY")
    if not api_key:
        return {
            "nodes": [],
            "edges": [],
            "message": "Missing URLSCAN_API_KEY in API vault. Get one at https://urlscan.io/",
        }

    url = entity.name.strip()

    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"http://{url}"
        parsed = urlparse(url)

    domain = parsed.netloc or parsed.path.split("/")[0]
    if domain:
        domain_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=domain,
                kind="domain",
                description=f"Extracted from URL: {entity.name}",
            ),
        )
        nodes.append(domain_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=domain_ent.id,
                    relation="contains_domain",
                ),
            )
        )

    submit = requests.post(
        "https://urlscan.io/api/v1/scan/",
        headers={
            "API-Key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "url": url,
            "visibility": "private",
        },
        timeout=20,
    )
    submit.raise_for_status()
    submit_data = submit.json()
    uuid = submit_data.get("uuid")

    if not uuid:
        return {
            "nodes": [n.dict() for n in nodes],
            "edges": [e.dict() for e in edges],
            "message": "URLScan submission failed",
        }

    data = None
    for attempt in range(6):
        time.sleep(10)
        result = requests.get(
            f"https://urlscan.io/api/v1/result/{uuid}/",
            timeout=20,
        )
        if result.status_code == 200:
            data = result.json()
            break
        if result.status_code != 404:
            result.raise_for_status()

    if not data:
        return {
            "nodes": [n.dict() for n in nodes],
            "edges": [e.dict() for e in edges],
            "message": f"URLScan result not ready after 60s. Check: https://urlscan.io/result/{uuid}/",
        }

    screenshot_url = data.get("task", {}).get("screenshotURL")
    page = data.get("page", {})
    verdicts = data.get("verdicts", {}).get("overall", {})

    malicious = verdicts.get("malicious", False)
    score = verdicts.get("score", 0)
    categories = verdicts.get("categories", [])

    status_code = page.get("status", 0)
    title = page.get("title", "")
    server = page.get("server", "")

    info_parts = [
        f"Status: {status_code}",
        f"Title: {title}" if title else None,
        f"Server: {server}" if server else None,
        f"Malicious: {malicious}",
        f"Score: {score}",
    ]
    info_parts = [p for p in info_parts if p]

    analysis_ent = store.create_entity(
        owner=owner,
        payload=EntityCreate(
            case_id=entity.case_id,
            name=f"URLScan: {'MALICIOUS' if malicious else 'Clean'}",
            kind="threat" if malicious else "analysis",
            description=", ".join(info_parts),
        ),
    )
    nodes.append(analysis_ent)
    edges.append(
        store.create_relationship(
            owner=owner,
            payload=RelationshipCreate(
                source_entity_id=entity.id,
                target_entity_id=analysis_ent.id,
                relation="scanned_as",
            ),
        )
    )

    if screenshot_url:
        screenshot_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name="URL Screenshot",
                kind="screenshot",
                description=screenshot_url,
            ),
        )
        nodes.append(screenshot_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=screenshot_ent.id,
                    relation="visualized_as",
                ),
            )
        )

    ips = set()
    for entry in data.get("lists", {}).get("ips", []):
        ips.add(entry)

    for ip in list(ips)[:5]:
        ip_ent = store.create_entity(
            owner=owner,
            payload=EntityCreate(
                case_id=entity.case_id,
                name=ip,
                kind="ip",
                description=f"IP contacted by {entity.name}",
            ),
        )
        nodes.append(ip_ent)
        edges.append(
            store.create_relationship(
                owner=owner,
                payload=RelationshipCreate(
                    source_entity_id=entity.id,
                    target_entity_id=ip_ent.id,
                    relation="contacts",
                ),
            )
        )

    return {"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}
