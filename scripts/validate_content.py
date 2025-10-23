# scripts/validate_content.py
import re, glob, pathlib, datetime as dt
from scripts.gpt_call import chat

CONTENT_GLOB = "output/content/**/*.md"

def newest_markdown() -> pathlib.Path | None:
    files = [pathlib.Path(p) for p in glob.glob(CONTENT_GLOB, recursive=True)]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None

md_path = newest_markdown()
if not md_path:
    print("ℹ️ No generated content found. Skipping validation.")
    raise SystemExit(0)

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

# --- quick quantitative checks
word_count = len(re.findall(r"\w+", text))
h2_count   = len(re.findall(r"(?m)^##\s", text))
h3_count   = len(re.findall(r"(?m)^###\s", text))
bullets    = len(re.findall(r"(?m)^\s*[-*+]\s", text))

score = 100
if word_count < 300: score -= 20
if h2_count   < 3:   score -= 20
if bullets    < 3:   score -= 10
if h3_count   < 1:   score -= 5
score = max(0, min(100, score))

now = dt.datetime.utcnow()
stamp = now.strftime("%Y%m%d-%H%M%S")

# --- write YAML front-matter report (.md)
report_md = f"""---
source_file: "{md_path}"
topic_slug: "{topic_slug}"
date: "{year}-{month}-{day}"
word_count: {word_count}
h2_count: {h2_count}
h3_count: {h3_count}
bullet_count: {bullets}
quality_score: {score}
generated_at_utc: "{now.isoformat()}Z"
---

# Validation Summary

- **File:** `{md_path.name}`
- **Topic:** {topic_slug.replace('-', ' ').title()}
- **Quality Score:** {score}/100
- **Headings:** H2={h2_count}, H3={h3_count}
- **Bullets:** {bullets}
- **Word Count:** {word_count}

*(Generated automatically by ContentVeritas validation pipeline.)*
"""

report_path = reports_dir / f"report-{stamp}.md"
report_path.write_text(report_md, encoding="utf-8")

# --- AI editorial review (unchanged)
review_prompt = (
    "You are a concise editor. Assess the Markdown for clarity, persuasiveness, and SEO.\n"
    "Return:\n"
    "1) Top 5 improvements (bullets)\n"
    "2) SEO checklist (title/H2s/keywords/meta)\n"
    "3) Revised hero headline + subhead\n"
    "≤ 250 words.\n\n"
    f"----- BEGIN CONTENT -----\n{text}\n----- END CONTENT -----"
)

review_md = chat([
    {"role": "system", "content": "You are a concise, no-nonsense content editor."},
    {"role": "user", "content": review_prompt},
])

review_path = reviews_dir / f"review-{stamp}.md"
review_path.write_text(review_md, encoding="utf-8")

print(f"✅ Wrote YAML report: {report_path}")
print(f"✅ Wrote review:      {review_path}")

