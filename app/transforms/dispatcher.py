from app.transforms.ip import run_ip_transforms
from app.transforms.domain import run_domain_transforms
from app.transforms.url import run_url_transforms
from app.transforms.email import run_email_transforms
from app.transforms.hash import run_hash_transforms
from app.transforms.phone import run_phone_transforms
from app.transforms.whois import run_whois_transforms
from app.transforms.shodan import run_shodan_transforms


TRANSFORM_MAP = {
    "ip": [
        {"name": "AbuseIPDB", "func": run_ip_transforms, "key": "ABUSEIPDB_API_KEY"},
        {"name": "Shodan", "func": run_shodan_transforms, "key": "SHODAN_API_KEY"},
    ],
    "domain": [
        {"name": "URLScan", "func": run_domain_transforms, "key": "URLSCAN_API_KEY"},
        {"name": "WHOIS", "func": run_whois_transforms, "key": "WHOISXML_API_KEY"},
    ],
    "url": [
        {"name": "URLScan", "func": run_url_transforms, "key": "URLSCAN_API_KEY"},
    ],
    "email": [
        {"name": "Hunter.io", "func": run_email_transforms, "key": "HUNTER_API_KEY"},
    ],
    "hash": [
        {"name": "VirusTotal", "func": run_hash_transforms, "key": "VIRUSTOTAL_API_KEY"},
    ],
    "phone": [
        {"name": "NumVerify", "func": run_phone_transforms, "key": "NUMVERIFY_API_KEY"},
    ],
}


def get_available_transforms(kind: str) -> list:
    kind = (kind or "").lower().strip()
    transforms = TRANSFORM_MAP.get(kind, [])
    return [{"name": t["name"], "key_required": t["key"]} for t in transforms]


def run_transforms(entity, owner: str, transform_name: str = "") -> dict:
    kind = (entity.kind or "").lower().strip()
    
    available = TRANSFORM_MAP.get(kind, [])
    
    if not available:
        return {"nodes": [], "edges": [], "message": f"No transforms available for kind='{entity.kind}'"}
    
    if transform_name:
        for t in available:
            if t["name"].lower() == transform_name.lower():
                return t["func"](entity, owner)
        return {"nodes": [], "edges": [], "message": f"Transform '{transform_name}' not found for kind='{entity.kind}'"}
    
    return available[0]["func"](entity, owner)
