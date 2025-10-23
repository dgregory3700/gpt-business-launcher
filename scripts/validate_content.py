# scripts/validate_content.py
import re, glob, pathlib, datetime as dt
from scripts.gpt_call import chat

# Find newest generated Markdown anywhere under output/content/**/**
CONTENT_GLOB = "output/content/**/*.md"

def newest_markdown() -> pathlib.Path | None:
    files = [pathlib.Path(p) for p in glob.glob(CONTENT_GLOB, recursive=True)]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None

md_path = newest_markdown()
if not md_path:
    print("ℹ️ No generated content found. Skipping validation.")
    raise SystemExit(0)

# Infer date + topic from the content file path:
# output/content/YYYY/MM/DD/<topic-slug>/<file>.md
parts = md_path.parts
year, month, day, topic_slug = "9999", "99", "99", "topic"
try:
    idx = parts.index("content")
    year, month, day, topic_slug = parts[idx+1], parts[idx+2], parts[idx+3], parts[idx+4]
except Exception:
    pass

reports_dir = pathlib.Path("output") / "reports" / year / month / day / topic_slug
reviews_dir = pathlib.Path("output") / "reviews" / year / month / day / topic_slug
reports_dir.mkdir(parents=True, exist_ok=True)
reviews_dir.mkdir(parents=True, exist_ok=True)

text = md_path.read_text(encoding="utf-8")

# -------- Simple quantitative checks --------
word_count = len(re.findall(r"\w+", text))
h2_count   = len(re.findall(r"(?m)^##\s", text))
h3_count   = len(re.findall(r"(?m)^###\s", text))
bullets    = len(re.findall(r"(?m)^\s*[-*+]\s", text))

quality = 100
if word_count < 300: quality -= 20
if h2_count   < 3:   quality -= 20
if bullets    < 3:   quality -= 10
if h3_count   < 1:   quality -= 5
quality = max(0, min(100, quality))

now = dt.datetime.utcnow()
stamp = now.strftime("%Y%m%d-%H%M%S")

# -------- YAML front-matter REPORT (.md) --------
report_md = f"""---
source_file: "{md_path}"
topic_slug: "{topic_slug}"
date: "{year}-{month}-{day}"
word_count: {word_count}
h2_count: {h2_count}
h3_count: {h3_count}
bullet_count: {bullets}
quality_score: {quality}
generated_at_utc: "{now.isoformat()}Z"
---

# Validation Summary

- **File:** `{md_path.name}`
- **Topic:** {topic_slug.replace('-', ' ').title()}
- **Quality Score:** {quality}/100
- **Headings:** H2={h2_count}, H3={h3_count}
- **Bullets:** {bullets}
- **Word Count:** {word_count}

*(Generated automatically by the validation pipeline.)*
"""

report_path = reports_dir / f"report-{stamp}.md"
report_path.write_text(report_md, encoding="utf-8")

# -------- AI editorial review (now also YAML front matter) --------
review_request = (
    "You are a concise copy editor and SEO strategist. Assess the Markdown for clarity, "
    "persuasiveness, and SEO. Return <= 250 words with:\n"
    "1) Top 5 improvements (bullets)\n"
    "2) SEO checklist (title/H2s/keywords/meta)\n"
    "3) Revised hero headline + subhead\n\n"
    "----- BEGIN CONTENT -----\n"
    f"{text}\n"
    "----- END CONTENT -----"
)

review_body = chat([
    {"role": "system", "content": "You are a concise, no-nonsense content editor."},
    {"role": "user", "content": review_request},
])

review_front_matter = f"""---
source_file: "{md_path}"
topic_slug: "{topic_slug}"
date: "{year}-{month}-{day}"
linked_report: "{report_path}"
quality_score: {quality}
generated_at_utc: "{now.isoformat()}Z"
---
"""

review_path = reviews_dir / f"review-{stamp}.md"
review_path.write_text(review_front_matter + "\n" + review_body, encoding="utf-8")

print(f"✅ Wrote YAML report: {report_path}")
print(f"✅ Wrote YAML review: {review_path}")
