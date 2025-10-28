
from __future__ import annotations
from typing import Iterable, Dict, Any, Tuple
from pathlib import Path
import time

# Import the user's parser directly from their project path if needed.
# For this standalone adapter, we expect to run from the repo root:
#   python adapters/faq_ingest_adapter.py --faq data/banking_faq_30plus.txt
try:
    from chatbot_for_bank_main.tools.faq_generator.parser import FAQParser  # when installed as a package
except Exception:
    # Fallback to relative path import when running inside the repo folder
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from tools.faq_generator.parser import FAQParser  # type: ignore

from graph_mem import GraphMem

def _entry_to_text(entry: Dict[str, Any]) -> Tuple[str, str]:
    """Return (id_text, blob_text) to store in GraphMem.
    id_text is short for traceability, blob_text is the content used for retrieval.
    """
    cat = entry.get("category") or ""
    q = entry.get("question") or ""
    a = entry.get("answer") or ""
    aliases = ", ".join(entry.get("aliases") or [])
    next_steps = "\n".join(f"- {s}" for s in (entry.get("next_steps") or []))
    tags = ", ".join(entry.get("tags") or [])

    id_text = f"[{cat}] Q: {q}"
    blob = "\n".join([
        f"[CATEGORY] {cat}",
        f"Q: {q}",
        f"A: {a}",
        (f"ALIASES: {aliases}" if aliases else ""),
        (f"NEXT_STEPS:\n{next_steps}" if next_steps else ""),
        (f"TAGS: {tags}" if tags else ""),
    ])
    blob = "\n".join([line for line in blob.splitlines() if line.strip()])
    return id_text, blob

def ingest_faq_to_graph(faq_path: str, gm: GraphMem) -> list[int]:
    parser = FAQParser()
    entries = parser.parse_file(Path(faq_path))
    ids: list[int] = []
    now = time.time()
    # Entries are objects (pydantic?) – normalize to dict
    norm_entries = []
    for e in entries:
        if hasattr(e, "model_dump"):
            norm_entries.append(e.model_dump())
        elif isinstance(e, dict):
            norm_entries.append(e)
        else:
            # fallback best-effort
            norm_entries.append(e.__dict__)
    for i, e in enumerate(norm_entries):
        id_text, blob = _entry_to_text(e)
        idx = gm.add(blob, ts=now + i)
        ids.append(idx)
    return ids
