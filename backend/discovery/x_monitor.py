import os, logging, httpx
from datetime import datetime, timedelta, timezone
from database import SessionLocal
from models import Release, Source
from verification.verifier import is_official

log = logging.getLogger("x_monitor")
ACCOUNTS = {"OpenAI": "OpenAI", "AnthropicAI": "Anthropic", "GoogleAI": "Google", "xai": "xAI", "AIatMeta": "Meta AI",
            "deepseek_ai": "DeepSeek", "Microsoft": "Microsoft", "nvidia": "NVIDIA", "github": "GitHub", "huggingface": "Hugging Face"}

def run_x():
    if os.getenv("X_DISCOVERY_ENABLED", "false").lower() != "true" or not os.getenv("X_BEARER_TOKEN"):
        return
    db = SessionLocal()
    try:
        start = (datetime.now(timezone.utc) - timedelta(hours=int(os.getenv("X_LOOKBACK_HOURS", 6)))).strftime("%Y-%m-%dT%H:%M:%SZ")
        q = "(" + " OR ".join(f"from:{a}" for a in ACCOUNTS) + ") has:links -is:retweet"
        r = httpx.get("https://api.x.com/2/tweets/search/recent", timeout=20,
                      headers={"Authorization": f"Bearer {os.environ['X_BEARER_TOKEN']}"},
                      params={"query": q, "start_time": start, "max_results": 50,
                              "tweet.fields": "created_at,entities,author_id", "expansions": "author_id", "user.fields": "username"})
        r.raise_for_status(); data = r.json()
        users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
        for t in data.get("data", []):
            if db.query(Release).filter_by(source_post_id=t["id"]).first(): continue
            author = users.get(t["author_id"], "")
            company = next((c for a, c in ACCOUNTS.items() if a.lower() == author.lower()), None)
            src = db.query(Source).filter_by(company=company).first() if company else None
            urls = [u.get("expanded_url") for u in t.get("entities", {}).get("urls", []) if u.get("expanded_url")]
            official = next((u for u in urls if src and is_official(u, src.official_domain)), None)
            if official:
                dup = db.query(Release).filter_by(official_url=official).first()
                if dup:  # official feed already has it: enrich, don't duplicate
                    dup.source_post_id = t["id"]; dup.x_author = author; dup.discovered_from_x_at = datetime.utcnow(); continue
            db.add(Release(title=t["text"][:300], tool_name=t["text"][:120], company=company or author,
                           official_url=official or f"https://x.com/{author}/status/{t['id']}",
                           discovery_source="X", discovery_url=f"https://x.com/{author}/status/{t['id']}",
                           source_post_id=t["id"], x_author=author, discovered_from_x_at=datetime.utcnow(),
                           verification_status="NEEDS_VERIFICATION" if official else "DISCOVERED_FROM_X",
                           official_content=t["text"]))
        db.commit()
        # promote candidates once an official URL is confirmed (never from X alone)
        for c in db.query(Release).filter_by(verification_status="NEEDS_VERIFICATION", discovery_source="X"):
            try:
                if httpx.get(c.official_url, timeout=15, follow_redirects=True).status_code == 200:
                    c.verification_status = "VERIFIED"; c.verified_at = datetime.utcnow()
            except Exception as ex:
                log.warning("verify X candidate %s: %s", c.id, ex)
        db.commit()
    except Exception as ex:
        db.rollback(); log.warning("X discovery failed: %s", ex)
    finally:
        db.close()