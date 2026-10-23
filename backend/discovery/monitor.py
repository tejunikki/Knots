import logging, httpx, feedparser
from datetime import datetime, timedelta
from database import SessionLocal
from models import Source, Release
from verification.verifier import verify

log = logging.getLogger("monitor")
KEYWORDS = ("model", " ai", "gpt", "claude", "gemini", "llama", "agent", "launch", "introducing", "release", "api", "copilot", "llm")
BROAD = {"Microsoft", "Adobe", "Amazon AWS", "NVIDIA", "GitHub"}

def check_source(db, s):
    if not s.rss_url:
        s.status = "NO_FEED_CONFIGURED"; return 0
    resp = httpx.get(s.rss_url, timeout=20, follow_redirects=True, headers={"User-Agent": "AIReleaseRadar/1.0"})
    resp.raise_for_status()
    new = 0
    for e in feedparser.parse(resp.content).entries[:15]:
        url, title = e.get("link"), e.get("title", "").strip()
        if not url or not title: continue
        if s.company in BROAD and not any(k in (" " + title.lower()) for k in KEYWORDS): continue
        existing = db.query(Release).filter_by(official_url=url).first()
        if existing: continue
        ok = verify(url, s)
        db.add(Release(
            tool_name=title[:200], title=title, company=s.company, official_url=url, announcement_url=url,
            release_date=(e.get("published") or "")[:40], discovery_source="OFFICIAL_FEED",
            verification_status="VERIFIED" if ok else "REJECTED",
            verified_at=datetime.utcnow() if ok else None,
            official_content=(e.get("summary") or "")[:4000]))
        new += 1
    return new

def run_all():
    db = SessionLocal()
    try:
        for s in db.query(Source).all():
            due = not s.last_checked or datetime.utcnow() - s.last_checked >= timedelta(minutes=s.check_interval or 5)
            if not due: continue
            try:
                n = check_source(db, s)
                if s.rss_url: s.status = "MONITORING"
                log.info("%s: %d new", s.company, n)
            except Exception as ex:
                db.rollback(); s = db.get(Source, s.id); s.status = "TEMPORARILY_UNAVAILABLE"
                log.warning("%s failed: %s", s.company, ex)
            s.last_checked = datetime.utcnow()
            db.commit()
    finally:
        db.close()