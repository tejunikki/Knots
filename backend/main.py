import os, hashlib, hmac, logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from itsdangerous import URLSafeTimedSerializer, BadSignature
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import User, Source, Release, Preference, Notification, Feedback
from discovery.sources import seed_sources
from scheduler import worker
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
SECRET = os.getenv("SECRET_KEY", "dev")
ser = URLSafeTimedSerializer(SECRET)

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    db = SessionLocal(); seed_sources(db); db.close()
    sch = worker.start()
    yield
    sch.shutdown(wait=False)

app = FastAPI(title="AI Release Radar", lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def hash_pw(p, salt=None):
    salt = salt or os.urandom(16).hex()
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 200_000).hex()

def check_pw(p, stored):
    salt = stored.split("$")[0]
    return hmac.compare_digest(hash_pw(p, salt), stored)

def current_user(authorization: str = Header(""), db: Session = Depends(get_db)):
    try: uid = ser.loads(authorization.replace("Bearer ", ""), max_age=60 * 60 * 24 * 7)
    except BadSignature: raise HTTPException(401, "Please log in again")
    u = db.get(User, uid)
    if not u: raise HTTPException(401, "Unknown user")
    return u

class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    profession: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str
class LoginIn(BaseModel):
    email: EmailStr; password: str
class PrefsIn(BaseModel):
    interests: List[str]
class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5); review_text: Optional[str] = None

def rel_out(r):
    return {c.name: getattr(r, c.name) for c in Release.__table__.columns if c.name != "official_content"}

# ---------- Public (no login) ----------

@app.get("/api/releases")
def releases(db: Session = Depends(get_db)):
    return [rel_out(r) for r in db.query(Release).order_by(Release.detected_at.desc()).limit(60)]

@app.get("/api/releases/{rid}")
def release(rid: int, db: Session = Depends(get_db)):
    r = db.get(Release, rid)
    if not r: raise HTTPException(404, "Release not found")
    return rel_out(r)

@app.get("/api/sources")
def sources(db: Session = Depends(get_db)):
    return [{c.name: getattr(s, c.name) for c in Source.__table__.columns} for s in db.query(Source)]

@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    done = db.query(Release).filter(Release.notified_at.isnot(None)).all()
    secs = [(r.notified_at - r.detected_at).total_seconds() for r in done if r.detected_at]
    return {"sources": db.query(Source).count(), "detected": db.query(Release).count(),
            "verified": db.query(Release).filter_by(verification_status="VERIFIED").count(),
            "notifications": db.query(Notification).count(),
            "avg_alert_minutes": round(sum(secs) / len(secs) / 60, 1) if secs else None}

# ---------- Accounts ----------

@app.post("/api/signup")
def signup(b: SignupIn, db: Session = Depends(get_db)):
    if b.password != b.confirm_password: raise HTTPException(400, "Passwords do not match")
    if db.query(User).filter_by(email=b.email.lower()).first(): raise HTTPException(409, "Email already registered. Please log in.")
    u = User(name=b.name.strip(), profession=b.profession.strip(), email=b.email.lower(), password_hash=hash_pw(b.password))
    db.add(u); db.commit()
    return {"token": ser.dumps(u.id)}

@app.post("/api/login")
def login(b: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=b.email.lower()).first()
    if not u or not check_pw(b.password, u.password_hash): raise HTTPException(401, "Wrong email or password")
    return {"token": ser.dumps(u.id)}

# ---------- Login required ----------

@app.get("/api/me")
def me(u: User = Depends(current_user), db: Session = Depends(get_db)):
    ints = [p.interest for p in db.query(Preference).filter_by(user_id=u.id)]
    return {"name": u.name, "profession": u.profession, "email": u.email, "created_at": u.created_at, "interests": ints}

@app.put("/api/preferences")
def prefs(b: PrefsIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(Preference).filter_by(user_id=u.id).delete()
    for i in set(b.interests): db.add(Preference(user_id=u.id, interest=i))
    db.commit(); return {"ok": True}

@app.post("/api/releases/{rid}/feedback")
def feedback(rid: int, b: FeedbackIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    db.add(Feedback(user_id=u.id, release_id=rid, rating=b.rating, review_text=b.review_text)); db.commit()
    return {"ok": True}

@app.get("/api/notifications")
def notifications(u: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Notification, Release).join(Release, Release.id == Notification.release_id)\
             .filter(Notification.user_id == u.id).order_by(Notification.sent_at.desc()).all()
    return [{"release_id": r.id, "tool_name": r.tool_name, "company": r.company, "sent_at": n.sent_at, "status": n.status} for n, r in rows]

app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True))