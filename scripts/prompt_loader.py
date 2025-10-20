from pathlib import Path

def load_prompt(path: str, **vars) -> str:
    text = Path(path).read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text
