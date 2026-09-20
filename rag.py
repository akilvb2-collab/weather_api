from pathlib import Path
import re
from typing import Dict, List, Set


KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def _words(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def retrieve(query: str, limit: int = 3) -> List[Dict[str, str]]:
    query_words = _words(query)
    matches = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        score = len(query_words & _words(content))
        if score:
            matches.append({"source": path.name, "content": content, "score": score})

    matches.sort(key=lambda item: (-int(item["score"]), item["source"]))
    return matches[:limit] 