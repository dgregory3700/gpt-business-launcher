# scripts/validate_content.py
import json, glob, os, pathlib, datetime as dt
from scripts.gpt_call import chat

CONTENT_GLOB = "output/content/**/*.md"  # recurse
REPORTS_DIR   = pathlib.Path("output/reports")
REVIEWS_DIR   = pathlib.Path("output/reviews")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

def newest_markdown() -> pathlib.Path | None:
    files = [pathlib.Path(p) for p in glob.glob(CONTENT_GLOB, recursive=True)]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None

md_path = newest_markdown()
if not md_path:
    print("No content files found for validation.")
    raise SystemExit(0)

text = md_path.read_text(encoding="utf-8")
ts = dt.datetime.utcnow()

# simple quantitative checks
report = {
    "file": str(md_path),
    "bytes": len(text.encode("utf-8")),
    "lines": len(text.splitlines()),
    "has_h2": "## " in text,
    "has_h3": "### " in text,
    "generated_at_utc": ts.isoformat() + "Z",
}

# LLM editorial review
messages = [
    {"role": "system", "content": "You are a precise editor. Be concise and actionable."},
    {"role": "user", "content": f"Review the Markdown for clarity, structure, and SEO. Suggest 5 concrete improvements.\n\n---\n{text}"},
]
review_md = chat(messages)

# write outputs next to generic reports/reviews (flat), or nest by date if you prefer
rep_path = REPORTS_DIR / f"report-{ts:%Y%m%d-%H%M%S}.json"
rev_path = REVIEWS_DIR / f"review-{ts:%Y%m%d-%H%M%S}.md"
rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
rev_path.write_text(review_md, encoding="utf-8")

print(f"✅ Wrote report:  {rep_path}")
print(f"✅ Wrote review:  {rev_path}")
