from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from database import Base

def now(): return datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    profession = Column(String(80))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=now)

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    company = Column(String(80), unique=True)
    official_domain = Column(String(255))  # comma-separated allowed domains
    release_page = Column(String(500))
    rss_url = Column(String(500))
    api_url = Column(String(500))
    tier = Column(Integer, default=1)
    check_interval = Column(Integer, default=5)  # minutes
    last_checked = Column(DateTime)
    status = Column(String(30), default="MONITORING")

class Release(Base):
    __tablename__ = "releases"
    id = Column(Integer, primary_key=True)
    tool_name = Column(String(255))
    title = Column(String(500))
    company = Column(String(80))
    category = Column(String(50))
    official_url = Column(String(1000), unique=True, index=True)
    announcement_url = Column(String(1000))
    release_date = Column(String(40))
    detected_at = Column(DateTime, default=now)
    discovered_from_x_at = Column(DateTime)
    verified_at = Column(DateTime)
    processed_at = Column(DateTime)
    notified_at = Column(DateTime)
    verification_status = Column(String(30), default="NEEDS_VERIFICATION")
    summary = Column(Text)
    details = Column(Text)  # Gemini JSON
    discovery_source = Column(String(30), default="OFFICIAL_FEED")
    discovery_url = Column(String(1000))
    source_post_id = Column(String(40), unique=True)
    x_author = Column(String(80))
    official_content = Column(Text)

class Preference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    interest = Column(String(50))

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    release_id = Column(Integer, ForeignKey("releases.id"))
    sent_at = Column(DateTime, default=now)
    status = Column(String(30))
    __table_args__ = (UniqueConstraint("user_id", "release_id"),)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    release_id = Column(Integer, ForeignKey("releases.id"))
    rating = Column(Integer)
    review_text = Column(Text)
    created_at = Column(DateTime, default=now)