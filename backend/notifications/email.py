import os, json, logging, smtplib, ssl, httpx
from datetime import datetime
from html import escape
from models import User, Preference, Notification

log = logging.getLogger("email")

def build_html(r):
    d = json.loads(r.details or "{}")
    feats = "".join(f"<li>{escape(str(f))}</li>" for f in d.get("key_features", []))
    return f"""<div style="font-family:Arial;background:#0b1020;color:#e8ecff;padding:28px;max-width:560px">
<h2 style="color:#8ea2ff">AI RELEASE RADAR</h2><p>Something new just landed in AI.</p>
<h3>{escape(r.tool_name or "")}</h3><p><b>Company:</b> {escape(r.company or "")} &nbsp; <b>Category:</b> {escape(r.category or "")} &nbsp; <b>Date:</b> {escape(r.release_date or "")}</p>
<p><b>What it does:</b> {escape(str(d.get('what_it_does') or r.summary or ""))}</p><ul>{feats}</ul>
<p><b>Why it matters:</b> {escape(str(d.get('why_it_matters','')))}</p><p><b>Useful for:</b> {escape(str(d.get('useful_for','')))}</p>
<p>Verified official source: {escape(r.official_url or "")}</p>
<a href="{escape(r.official_url or "")}" style="background:#5b6cff;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none">VIEW OFFICIAL RELEASE</a></div>"""

def send_gmail(to, subject, html):
    from email.message import EmailMessage
    addr, pw = os.getenv("GMAIL_ADDRESS"), os.getenv("GMAIL_APP_PASSWORD")
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = f"AI Release Radar <{addr}>", to, subject
    msg.set_content("A new AI release matches your interests. Open this email in an HTML-capable client.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as s:
        s.login(addr, pw.replace(" ", ""))
        s.send_message(msg)
    return "DELIVERED"

def send_resend(to, subject, html):
    r = httpx.post("https://api.resend.com/emails", timeout=20,
                   headers={"Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}"},
                   json={"from": "AI Release Radar <onboarding@resend.dev>", "to": [to], "subject": subject, "html": html})
    if r.status_code >= 300:
        log.warning("Resend rejected email: %s %s", r.status_code, r.text[:200])
        return "FAILED"
    return "DELIVERED"
def send(to, subject, html):
    try:
        if os.getenv("GMAIL_ADDRESS") and os.getenv("GMAIL_APP_PASSWORD"):
            return send_gmail(to, subject, html)
        if os.getenv("RESEND_API_KEY"):
            return send_resend(to, subject, html)
        return "SKIPPED_NO_KEY"
    except Exception as ex:
        log.warning("email failed: %s", ex)
        return "FAILED"

def notify_release(db, r):
    users = db.query(User).join(Preference, Preference.user_id == User.id).filter(Preference.interest == r.category).all()
    for u in users:
        if db.query(Notification).filter_by(user_id=u.id, release_id=r.id).first(): continue  # no duplicate emails
        status = send(u.email, f"New in AI: {r.tool_name}", build_html(r))
        db.add(Notification(user_id=u.id, release_id=r.id, status=status))
    r.notified_at = datetime.utcnow()
    db.commit()