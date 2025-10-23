# scripts/generate_content.py
import os, re
import pathlib
import datetime as dt
from scripts.gpt_call import chat  # our helper that calls OpenAI

# ----- helpers -----
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s-]", "", text)          # keep letters/numbers/spaces/hyphens
    text = re.sub(r"\s+", "-", text)                  # spaces -> hyphens
    text = re.sub(r"-{2,}", "-", text).strip("-")     # collapse/trim hyphens
    return text or "topic"

# ----- inputs -----
TOPIC = os.getenv("TOPIC", "AI-powered micro-SaaS for niche creators")
topic_slug = slugify(TOPIC)

# dated folder: output/content/YYYY/MM/DD/<topic-slug>
ts = dt.datetime.utcnow()
root = pathlib.Path("output") / "content" / f"{ts:%Y}" / f"{ts:%m}" / f"{ts:%d}" / topic_slug
root.mkdir(parents=True, exist_ok=True)

# ----- prompt -----
prompt = (
    f"Create 2 short, SEO-friendly blog outlines about the topic: “{TOPIC}”. "
    "Return valid Markdown with H2/H3 sections and bullet points. "
    "Keep it concise and useful for a busy reader."
)

messages = [
    {"role": "system", "content": "You are an SEO-savvy content creator for startups."},
    {"role": "user", "content": prompt},
]

# ----- call model -----
md = chat(messages)

# prepend a tiny metadata block (table) for quick context
header = (
    f"| title | topic | model | generated_at_utc |\n"
    f"|---|---|---|---|\n"
    f"| Auto content for {TOPIC} | {TOPIC} | gpt-4o-mini | {ts.isoformat()}Z |\n\n"
)

# ----- write file -----
out_path = root / f"content-{ts:%Y%m%d-%H%M%S}.md"
out_path.write_text(header + md, encoding="utf-8")

print(f"✅ Saved generated content to {out_path}")
