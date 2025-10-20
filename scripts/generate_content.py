import os, pathlib, datetime
from scripts.gpt_call import chat
from scripts.prompt_loader import load_prompt

# Where we'll store generated files
OUTPUT_ROOT = pathlib.Path("output/content")

# Topic comes from the workflow input (fallback provided)
TOPIC = os.getenv("TOPIC", "AI-powered micro-SaaS for niche creators")
PROMPT_PATH = "prompts/F_landing_page.md"

# Load the prompt from file and substitute variables
prompt = load_prompt(PROMPT_PATH, TOPIC=TOPIC)

messages = [
    {"role": "system", "content": "You are an SEO-savvy copywriter for startups."},
    {"role": "user", "content": prompt},
]

md = chat(messages)

# Dated directory: output/content/YYYY/MM/DD/
stamp = datetime.datetime.utcnow()
dated_dir = OUTPUT_ROOT / stamp.strftime("%Y/%m/%d")
dated_dir.mkdir(parents=True, exist_ok=True)

# Optional: YAML front matter for downstream tools
front_matter = f"""---
title: "Landing page draft for {TOPIC}"
topic: "{TOPIC}"
model: "gpt-4o-mini"
generated_at_utc: "{stamp.isoformat()}Z"
---
"""

outfile = dated_dir / f"landing-{stamp.strftime('%Y%m%d-%H%M%S')}.md"
outfile.write_text(front_matter + "\n" + md, encoding="utf-8")
print(f"✅ Saved {outfile}")

