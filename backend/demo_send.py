import argparse, json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
load_dotenv()
from database import SessionLocal
from models import User, Preference, Release, Notification
from ai.gemini import summarize
from notifications.email import send, build_html

ap = argparse.ArgumentParser()
ap.add_argument("email", help="registered user's email")
ap.add_argument("--days", type=int, default=14, help="how far back to look")
ap.add_argument("--limit", type=int, default=3, help="max emails to send")
ap.add_argument("--all", action="store_true", help="ignore interests (send any category)")
ap.add_argument("--force", action="store_true", help="resend even if already sent")
a = ap.parse_args()

def when(r):
    s = r.release_date or ""
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return r.detected_at
    if d.tzinfo: d = d.astimezone(timezone.utc).replace(tzinfo=None)
    return d

db = SessionLocal()
u = db.query(User).filter_by(email=a.email.lower()).first()
if not u:
    raise SystemExit("No user with that email. Sign up in the app first.")
interests = [p.interest for p in db.query(Preference).filter_by(user_id=u.id)]
print("User:", u.email, "| interests:", interests)

cutoff = datetime.utcnow() - timedelta(days=a.days)
rels = [r for r in db.query(Release).filter_by(verification_status="VERIFIED").all() if when(r) and when(r) >= cutoff]
rels.sort(key=when, reverse=True)
print(f"Verified releases in the last {a.days} days: {len(rels)}")

sent = 0
for r in rels:
    if sent >= a.limit: break
    if not r.processed_at or not r.details:
        d = summarize(r)
        r.summary, r.category, r.details, r.processed_at = d.get("summary"), d["category"], json.dumps(d), datetime.utcnow()
        db.commit()
    if not a.all and r.category not in interests:
        continue
    old = db.query(Notification).filter_by(user_id=u.id, release_id=r.id).first()
    if old and not a.force:
        continue
    if old:
        db.delete(old); db.commit()
    status = send(u.email, f"New in AI: {r.tool_name}", build_html(r))
    db.add(Notification(user_id=u.id, release_id=r.id, status=status))
    r.notified_at = datetime.utcnow()
    db.commit()
    print(f"{status}: [{r.company}] {r.tool_name}")
    sent += 1

if sent == 0:
    print("Nothing sent. Try --all (ignore interests), --force (resend), or a larger --days.")
