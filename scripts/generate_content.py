import os, pathlib, datetime
from scripts.gpt_call import chat  # import from scripts/ package

OUTPUT_DIR = pathlib.Path("output/content")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOPIC = "a first-week content plan for a new AI-powered micro-SaaS"

prompt = (
    f"Create 2 short, SEO-friendly blog outlines about {TOPIC}. "
    "Return valid Markdown with H2/H3 sections and bullet points."
)

messages = [
    {"role": "system", "content": "You are an SEO-savvy content creator for startups."},
    {"role": "user", "content": prompt}
]

md = chat(messages)

ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
out_path = OUTPUT_DIR / f"content-{ts}.md"
out_path.write_text(md, encoding="utf-8")

print(f"Saved {out_path}")
