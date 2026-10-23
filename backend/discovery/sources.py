from models import Source

# rss_url=None -> no official feed known; fill in release_page/rss_url yourself.
SEED = [
 ("OpenAI","openai.com","https://openai.com/news/","https://openai.com/news/rss.xml",1),
 ("Anthropic","anthropic.com,claude.com","https://www.anthropic.com/news",None,1),
 ("Google","blog.google,deepmind.google,google.dev","https://blog.google/technology/ai/","https://blog.google/technology/ai/rss/",1),
 ("xAI","x.ai","https://x.ai/news",None,1),
 ("Meta AI","ai.meta.com,meta.com","https://ai.meta.com/blog/",None,1),
 ("DeepSeek","deepseek.com","https://api-docs.deepseek.com/updates",None,1),
 ("Microsoft","microsoft.com","https://blogs.microsoft.com/ai/","https://blogs.microsoft.com/ai/feed/",2),
 ("Adobe","adobe.com","https://blog.adobe.com/","https://blog.adobe.com/feed",2),
 ("Amazon AWS","aws.amazon.com,amazon.science","https://aws.amazon.com/blogs/machine-learning/","https://aws.amazon.com/blogs/machine-learning/feed/",2),
 ("NVIDIA","nvidia.com","https://blogs.nvidia.com/","https://blogs.nvidia.com/feed/",2),
 ("GitHub","github.blog,github.com","https://github.blog/changelog/","https://github.blog/changelog/feed/",2),
 ("Hugging Face","huggingface.co","https://huggingface.co/blog","https://huggingface.co/blog/feed.xml",2),
]

def seed_sources(db):
    for c, d, p, r, t in SEED:
        if not db.query(Source).filter_by(company=c).first():
            db.add(Source(company=c, official_domain=d, release_page=p, rss_url=r, tier=t, check_interval=5 if t == 1 else 10))
    db.commit()