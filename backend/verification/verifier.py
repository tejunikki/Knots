from urllib.parse import urlparse

def is_official(url, domains):
    host = (urlparse(url or "").hostname or "").lower()
    return any(host == d.strip() or host.endswith("." + d.strip()) for d in domains.split(","))

def verify(url, source):
    """Deterministic: URL must be https and on the company's official domain."""
    return bool(url) and url.startswith("https://") and is_official(url, source.official_domain)