# adapters/faq_ingest_adapter.py
from __future__ import annotations

import time
import re
from pathlib import Path
from typing import Iterable

from graph_mem import GraphMem

FAQ_ITEM_RE = re.compile(
    r"""
    ^\s*\[CATEGORY:\s*(?P<category>[^\]]+)\]\s*?\n
    Q:\s*(?P<q>.*?)\n
    A:\s*(?P<a>.*?)\n
    ALIASES:\s*(?P<aliases>.*?)\n
    (?:NEXT_STEPS:\s*(?P<next_steps>(?:-.*?\n)+))?
    TAGS:\s*(?P<tags>.*?)(?:\n{2,}|\Z)
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def parse_faq_blocks(text: str):
    for m in FAQ_ITEM_RE.finditer(text):
        yield {
            "category": _norm(m.group("category")),
            "q": _norm(m.group("q")),
            "a": _norm(m.group("a")),
            "aliases": [a.strip() for a in _norm(m.group("aliases")).split(",") if a.strip()],
            "next_steps": [re.sub(r"^\s*-\s*", "", ln).strip()
                           for ln in (m.group("next_steps") or "").splitlines() if ln.strip()],
            "tags": [t.strip() for t in _norm(m.group("tags")).split(",") if t.strip()],
        }

def serialise_block(b: dict) -> str:
    parts = [
        f"[CATEGORY] {b['category']}",
        f"Q: {b['q']}",
        f"A: {b['a']}",
        f"ALIASES: {', '.join(b['aliases'])}" if b['aliases'] else "ALIASES:",
        "NEXT_STEPS:\n" + "\n".join(f"- {s}" for s in b['next_steps']) if b['next_steps'] else "NEXT_STEPS:",
        f"TAGS: {', '.join(b['tags'])}" if b['tags'] else "TAGS:",
    ]
    return "\n".join(parts)

def ingest_faq_to_graph(faq_path: str | Path, gm: GraphMem) -> int:
    """
    Parsuje plik FAQ i dodaje każdy rekord jako Fact do GraphMem.
    Zwraca liczbę załadowanych faktów.
    """
    text = Path(faq_path).read_text(encoding="utf-8", errors="ignore")
    count = 0
    now = time.time()
    for block in parse_faq_blocks(text):
        payload = serialise_block(block)
        gm.add(payload, ts=now)
        count += 1
    return count
