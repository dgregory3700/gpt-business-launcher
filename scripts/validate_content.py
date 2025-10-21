# scripts/validate_content.py
import os, re, json, pathlib, datetime
from scripts.gpt_call import chat  # uses your OpenAI helper

CONTENT_DIR = pathlib.Path("output/content")
REPORTS_DIR = pathlib.Path("output/reports")
REVIEWS_DIR = pathlib.Path("output/reviews")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

def latest_markdown(root: pathlib.Path):
    files = list(root.rglob("*.md"))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None

md_file = latest_markdown(CONTENT_DIR)
if not md_file:
    print("ℹ️ No generated content found. Skipping validation.")
    raise SystemExit(0)

text = md_file.read_text(encoding="utf-8")

# --- simple heuristic checks
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

stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")

# --- write a JSON metrics report
report = {
    "file": str(md_file),
    "word_count": word_count,
    "h2_count": h2_count,
    "h3_count": h3_count,
    "bullet_count": bullets,
    "quality_score": score,
    "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
}
report_path = REPORTS_DIR / f"report-{stamp}.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

# --- AI editorial review (short, actionable)
review_prompt = (
    "You are a rigorous copy editor and SEO strategist. "
    "Assess the following Markdown landing page draft for clarity, persuasiveness, and SEO. "
    "Return a concise review with:\n"
    "1) Top 5 improvements (bullet list)\n"
    "2) SEO checklist (title, H2s, keywords, meta description)\n"
    "3) A revised hero headline + subhead\n"
    "Keep it under 250 words.\n\n"
    "----- BEGIN CONTENT -----\n"
    f"{text}\n"
    "----- END CONTENT -----"
)

review_md = chat([
    {"role": "system", "content": "You are a concise, no-nonsense content editor."},
    {"role": "user", "content": review_prompt},
])

review_path = REVIEWS_DIR / f"review-{stamp}.md"
review_path.write_text(review_md, encoding="utf-8")

print(f"✅ Wrote metrics: {report_path}")
print(f"✅ Wrote review:  {review_path}")
