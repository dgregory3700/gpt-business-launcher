# scripts/validate_content.py
import json, glob, re
import pathlib, datetime as dt
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
# Defensive defaults
year, month, day, topic_slug = "9999", "99", "99", "topic"
try:
    # .../output/content/ YYYY  MM  DD  topic  file
    idx = parts.index("content")
    year, month, day = parts[idx+1], parts[idx+2], parts[idx+3]
    topic_slug = parts[idx+4]
except Exception:
    pass

reports_dir = pathlib.Path("output") / "reports" / year / month / day / topic_slug
reviews_dir = pathlib.Path("output") / "reviews" / year / month / day / topic_slug
reports_dir.mkdir(parents=True, exist_ok=True)
reviews_dir.mkdir(parents=True, exist_ok=True)

text = md_path.read_text(encoding="utf-8")

# -------- Simple quantitative checks (very lightweight) --------
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

# -------- JSON metrics report --------
report = {
    "source_file": str(md_path),
    "topic_slug": topic_slug,
    "date": f"{year}-{month}-{day}",
    "word_count": word_count,
    "h2_count": h2_count,
    "h3_count": h3_count,
    "bullet_count": bullets,
    "quality_score": score,
    "generated_at_utc": now.isoformat() + "Z",
}
report_path = reports_dir / f"report-{stamp}.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

# -------- AI editorial review (short, actionable) --------
review_prompt = (
    "You are a rigorous copy editor and SEO strategist. "
    "Assess the following Markdown for clarity, persuasiveness, and SEO. "
    "Return:\n"
    "1) Top 5 improvements (bullets)\n"
    "2) SEO checklist (title/H2s/keywords/meta)\n"
    "3) Revised hero headline + subhead\n"
    "≤ 250 words.\n\n"
    "----- BEGIN CONTENT -----\n"
    f"{text}\n"
    "----- END CONTENT -----"
)

review_md = chat([
    {"role": "system", "content": "You are a concise, no-nonsense content editor."},
    {"role": "user", "content": review_prompt},
])

review_path = reviews_dir / f"review-{stamp}.md"
review_path.write_text(review_md, encoding="utf-8")

print(f"✅ Wrote metrics: {report_path}")
print(f"✅ Wrote review:  {review_path}")

