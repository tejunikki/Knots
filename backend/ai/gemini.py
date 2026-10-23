import os, json, logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("gemini")
CATS = ["AI Agents", "AI Models", "AI Tools", "AI Products", "Coding", "Productivity", "Image Generation",
        "Video Generation", "Data Science", "Education", "Business", "Research"]

def _fallback(r):
    t = (r.title or "").lower()
    rules = [("AI Agents", ("agent",)), ("Coding", ("code", "copilot", "codex")), ("Image Generation", ("image",)),
             ("Video Generation", ("video",)), ("Research", ("research", "paper")), ("AI Tools", ("tool", "api", "sdk", "developer")),
             ("AI Models", ("model", "gpt", "claude", "gemini", "llama")), ("AI Products", ("launch", "introducing", "app", "product"))]
    cat = next((c for c, ks in rules if any(k in t for k in ks)), "AI Models")
    s = (r.official_content or r.title or "")[:400]
    return {"category": cat, "summary": s, "what_it_does": s, "key_features": [], "useful_for": "", "use_cases": [], "why_it_matters": ""}

def summarize(r):
    key = os.getenv("GEMINI_API_KEY")
    if not key: return _fallback(r)
    try:
        from google import genai
        prompt = (f"Using ONLY the verified text below, return JSON with keys: category (one of {CATS}), summary, what_it_does, "
                  "key_features (list), useful_for, use_cases (list), why_it_matters. Do not invent URLs, dates, or features.\n"
                  f"Company: {r.company}\nTitle: {r.title}\nContent: {(r.official_content or '')[:4000]}")
        resp = genai.Client(api_key=key).models.generate_content(
            model="gemini-2.5-flash", contents=prompt, config={"response_mime_type": "application/json"})
        d = json.loads(resp.text)
        if d.get("category") not in CATS: d["category"] = _fallback(r)["category"]
        return d
    except Exception as ex:
        log.warning("Gemini failed, using fallback: %s", ex)
        return _fallback(r)