# agent.py
# Minimal memory-aware agent for Banking FAQ backed by a graph memory (MVP).
# No __main__ here — run it from a notebook or another script.
from __future__ import annotations

import time
import re
from typing import Protocol, List

from graph_mem import GraphMem, Fact


class Model(Protocol):
    """Minimal protocol for pluggable text generation models."""
    def generate(self, prompt: str) -> str: ...


class HeuristicModel:
    """
    Extremely lightweight "generator":
    - Looks for the first line starting with "A:" inside the provided FACT blocks.
    - If nothing is found, returns the first non-empty line of the first FACT.
    - Otherwise returns a safe fallback.
    """
    _fact_block_re = re.compile(r"### FACT\n(.*?)(?=\n### FACT|\Z)", flags=re.S | re.M)

    def generate(self, prompt: str) -> str:
        facts = self._fact_block_re.findall(prompt) or []

        # 1) Try to extract 'A:' from top-ranked facts
        for fact in facts:
            m = re.search(r"^A:\s*(.+)$", fact, flags=re.M)
            if m:
                return m.group(1).strip()

        # 2) Otherwise, best-effort: return first informative line from first fact
        if facts:
            lines = [ln.strip() for ln in facts[0].splitlines() if ln.strip()]
            # Prefer second line (often 'Q:' is first), else the first line
            if len(lines) >= 2:
                return lines[1]
            return lines[0]

        # 3) Fallback
        return "Nie wiem na podstawie dostarczonych faktów."
    

class MemoryAwareAgent:
    """
    Agent that:
    - retrieves a context from GraphMem,
    - builds a prompt,
    - lets a pluggable Model generate an answer,
    - stores the dialogue into memory for continuity.
    """
    def __init__(self, memory: GraphMem, model: Model | None = None):
        self.memory = memory
        self.model = model or HeuristicModel()

    def build_prompt(self, user_msg: str, context: List[Fact]) -> str:
        context_text = "\n\n".join(f"### FACT\n{f.text}" for f in context)
        return (
            "You are a banking FAQ assistant. Use ONLY the provided facts to answer.\n"
            "If the answer is not covered, say you don't know.\n\n"
            f"{context_text}\n\n"
            f"User: {user_msg}\n"
            "Answer: "  # trailing space avoids returning bare 'Answer:' with trivial models
        )

    def reply(self, user_msg: str, top_k: int = 6) -> str:
        now = time.time()
        ctx = self.memory.retrieve(user_msg, now_ts=now, k=top_k)
        prompt = self.build_prompt(user_msg, ctx)
        answer = self.model.generate(prompt)
        # persist the interaction to memory for future rounds
        self.memory.add(f"USER: {user_msg}", ts=now)
        self.memory.add(f"ASSISTANT: {answer}", ts=now)
        return answer


def build_agent_from_faq(
    faq_path: str,
    tau: float = 0.35,
    k: int = 5,
    alpha: float = 0.7,
) -> MemoryAwareAgent:
    """
    Convenience helper:
    - creates GraphMem with given params,
    - ingests the FAQ file using your project's FAQParser adapter,
    - returns a ready-to-use MemoryAwareAgent.

    Supports both 'adapters' and 'adapter' module names.
    """
    gm = GraphMem(tau=tau, k=k, alpha=alpha)

    # Import ingest adapter lazily to support both folder names
    ingest = None
    try:
        from adapters import faq_ingest_adapter as ingest  # type: ignore
    except Exception:
        try:
            from adapter import faq_ingest_adapter as ingest  # type: ignore
        except Exception as e:
            raise ImportError(
                "Nie można zaimportować adaptera FAQ. Upewnij się, że masz "
                "'adapters/faq_ingest_adapter.py' lub 'adapter/faq_ingest_adapter.py'."
            ) from e

    ingest.ingest_faq_to_graph(faq_path, gm)
    return MemoryAwareAgent(gm)
