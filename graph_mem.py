
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Callable
import numpy as np
import math
import hashlib

Vector = np.ndarray
EmbedFn = Callable[[str], Vector]

def _hash_embed(text: str, dim: int = 256) -> Vector:
    """Deterministic, dependency-free embedding stub (for MVP)."""
    v = np.zeros(dim, dtype=np.float32)
    for tok in text.lower().split():
        h = hashlib.blake2b(tok.encode("utf-8"), digest_size=32).digest()
        for i in range(0, len(h), 2):
            idx = h[i] % dim
            val = (h[i+1] / 255.0)
            v[idx] += val
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def cosine(a: Vector, b: Vector) -> float:
    da = np.linalg.norm(a)
    db = np.linalg.norm(b)
    if da == 0 or db == 0: return 0.0
    return float(np.dot(a, b) / (da * db))

@dataclass
class Fact:
    text: str
    ts: float
    vec: Vector
    neigh: List[Tuple[int, float]] = field(default_factory=list)

class GraphMem:
    def __init__(self, embed: EmbedFn | None = None, tau: float = 0.35, k: int = 5, alpha: float = 0.7):
        self.embed = embed or _hash_embed
        self.tau = tau
        self.k = k
        self.alpha = alpha
        self.facts: list[Fact] = []

    def add(self, text: str, ts: float) -> int:
        vec = self.embed(text)
        sims = [(i, cosine(vec, f.vec)) for i, f in enumerate(self.facts)]
        sims = sorted([x for x in sims if x[1] >= self.tau], key=lambda x: -x[1])[: self.k]
        node = Fact(text=text, ts=ts, vec=vec, neigh=sims)
        self.facts.append(node)
        return len(self.facts) - 1

    def retrieve(self, query: str, now_ts: float, k: int | None = None) -> list[Fact]:
        k = k or self.k
        qv = self.embed(query)
        base = [(i, cosine(qv, f.vec)) for i, f in enumerate(self.facts)]
        base = sorted(base, key=lambda x: -x[1])[:k]
        hop = set(j for i, _ in base for (j, _) in self.facts[i].neigh)
        cand = {i for i, _ in base} | hop

        def recency(ts: float) -> float:
            days = max(0.0, (now_ts - ts) / 86400.0)
            return 1.0 / (1.0 + days)

        def score(i: int) -> float:
            f = self.facts[i]
            sim = cosine(qv, f.vec)
            return self.alpha * sim + (1.0 - self.alpha) * recency(f.ts)

        ranked = sorted(cand, key=lambda i: -score(i))[: 2 * k]
        return [self.facts[i] for i in ranked]
