import os, json, logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Release
from discovery.monitor import run_all
from discovery.x_monitor import run_x
from ai.gemini import summarize
from notifications.email import notify_release

log = logging.getLogger("worker")

def process_pending():
    db = SessionLocal()
    try:
        for r in db.query(Release).filter(Release.verification_status == "VERIFIED", Release.processed_at.is_(None)).all():
            try:
                d = summarize(r)
                r.summary, r.category, r.details, r.processed_at = d.get("summary"), d["category"], json.dumps(d), datetime.utcnow()
                db.commit()
                notify_release(db, r)
            except Exception as ex:
                db.rollback(); log.warning("process %s failed: %s", r.id, ex)
    finally:
        db.close()

def safe(fn):
    def w():
        try: fn()
        except Exception as ex: log.exception("job %s crashed: %s", fn.__name__, ex)
    return w

def start():
    s = BackgroundScheduler()
    s.add_job(safe(run_all), "interval", minutes=5, next_run_time=datetime.utcnow())
    s.add_job(safe(process_pending), "interval", minutes=1)
    s.add_job(safe(run_x), "interval", minutes=int(os.getenv("X_POLL_MINUTES", 15)))
    s.start()
    return