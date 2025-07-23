import yaml
import re
from pathlib import Path

def load_config(path: Path = Path(__file__).parent.parent / "config" / "settings.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def clean_text_with_config(text: str) -> str:
    config = load_config()
    patterns = [r["pattern"] for r in config.get("text_cleanup_regex", [])]

    for pattern in patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    return text.strip()
