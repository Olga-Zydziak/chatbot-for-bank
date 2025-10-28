# memory_qa.py
from __future__ import annotations

import time
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np
from graph_mem import GraphMem, Fact

# --- Parsowanie składowych FAQ ---
FAQ_A_RE = re.compile(r"^\s*A:\s*(?P<a>.+)$", re.IGNORECASE | re.MULTILINE)
FAQ_Q_RE = re.compile(r"^\s*Q:\s*(?P<q>.+)$", re.IGNORECASE | re.MULTILINE)
FAQ_CAT_RE = re.compile(r"^\s*\[CATEGORY\]\s*(?P<c>.+)$", re.IGNORECASE | re.MULTILINE)
FAQ_ALIASES_RE = re.compile(r"^\s*ALIASES:\s*(?P<al>.+)$", re.IGNORECASE | re.MULTILINE)

_WORD = re.compile(r"[0-9A-Za-zÀ-ÿąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+")

def _tok(s: str) -> List[str]:
    return [t.lower() for t in _WORD.findall(s)]

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    da, db = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if da == 0.0 or db == 0.0: return 0.0
    return float(np.dot(a, b) / (da * db))

def _recency(now_ts: float, ts: float) -> float:
    days = max(0.0, (now_ts - ts) / 86400.0)
    return 1.0 / (1.0 + days)

def _overlap_score(q_terms: set, d_terms: set) -> float:
    if not q_terms or not d_terms: return 0.0
    inter = len(q_terms & d_terms)
    union = len(q_terms | d_terms)
    return inter / union

def _contains_any(needle: set, hay: set, k: int = 1) -> bool:
    return len(needle & hay) >= k

@dataclass
class AnswerCandidate:
    fact: Fact
    sim: float
    rec: float
    lex: float
    score: float
    answer_text: str
    question_text: str
    aliases: List[str]
    category: Optional[str]

class MemoryQABot:
    """
    Hybrydowy retriever nad GraphMem:
      final_score = (1-lex_w)*[alpha*sim + (1-alpha)*rec] + lex_w*lex + alias/Q_boost
    gdzie:
      sim  – cosinus na embeddingach GraphMem,
      rec  – świeżość,
      lex  – Jaccard z tokenów (overlap),
      alias/Q_boost – dopalacz przy (prawie) dokładnym dopasowaniu Q lub ALIASES.
    """
    def __init__(self, gm: GraphMem,
                 alpha: float = 0.7,         # waga dense vs recency
                 min_sim: float = 0.5,       # minimalny próg podobieństwa gęstego
                 lex_weight: float = 0.4,    # udział składowej lexical
                 strict_alias_boost: float = 0.25,  # dopalacz dla (quasi) exact Q/ALIASES
                 ):
        self.gm = gm
        self.alpha = alpha
        self.min_sim = min_sim
        self.lex_weight = lex_weight
        self.strict_alias_boost = strict_alias_boost

        # Precompute dla lexical
        self._fact_terms: List[set] = []
        self._fact_q: List[str] = []
        self._fact_aliases: List[List[str]] = []
        for f in self.gm.facts:
            terms = set(_tok(f.text))
            self._fact_terms.append(terms)
            self._fact_q.append(self._extract_q(f.text))
            self._fact_aliases.append(self._extract_aliases(f.text))

    # --- ekstrakcja pól z Fact.text ---
    def _extract_a(self, text: str) -> str:
        m = FAQ_A_RE.search(text)
        return m.group("a").strip() if m else text.strip()

    def _extract_q(self, text: str) -> str:
        m = FAQ_Q_RE.search(text)
        return m.group("q").strip() if m else ""

    def _extract_cat(self, text: str) -> Optional[str]:
        m = FAQ_CAT_RE.search(text)
        return m.group("c").strip() if m else None

    def _extract_aliases(self, text: str) -> List[str]:
        m = FAQ_ALIASES_RE.search(text)
        if not m: return []
        raw = m.group("al")
        return [x.strip() for x in raw.split(",") if x.strip()]

    def _strict_match_boost(self, query: str, i: int) -> float:
        qnorm = query.strip().lower()
        if not qnorm: return 0.0
        if qnorm == self._fact_q[i].strip().lower():
            return self.strict_alias_boost
        for al in self._fact_aliases[i]:
            if qnorm == al.lower():
                return self.strict_alias_boost
        return 0.0

    def retrieve(self, query: str, now_ts: Optional[float] = None, k: int = 7) -> List[AnswerCandidate]:
        now_ts = now_ts or time.time()
        q_terms = set(_tok(query))

        # 1) shortlist z GraphMem (gęsta semantyka + recency)
        dense = self.gm.retrieve(query, now_ts=now_ts, k=max(10, k))

        # 2) lexical pre-filter przy silnych słowach (zmniejsza "przyciąganie" chargebacku)
        strong = {"pin", "zastrzec", "zastrzeż", "chargeback", "spór",
                  "przelew", "blokada", "karta", "limit", "limity"}
        if _contains_any(q_terms, strong, k=1):
            filtered = []
            for f in dense:
                try:
                    fid = self.gm.facts.index(f)
                except ValueError:
                    fid = 0
                if _contains_any(q_terms, self._fact_terms[fid], k=1):
                    filtered.append(f)
            dense = filtered or dense  # fallback gdy zbyt ciasno

        # 3) policz składowe i zbuduj ranking
        qv = self.gm.embed(query)
        out: List[AnswerCandidate] = []
        for idx, f in enumerate(dense):
            try:
                fid = self.gm.facts.index(f)
            except ValueError:
                fid = idx
            sim = _cosine(qv, f.vec)
            rec = _recency(now_ts, f.ts)
            dense_score = self.alpha * sim + (1.0 - self.alpha) * rec
            lex = _overlap_score(q_terms, self._fact_terms[fid])
            boost = self._strict_match_boost(query, fid)
            final = (1.0 - self.lex_weight) * dense_score + self.lex_weight * lex + boost

            out.append(AnswerCandidate(
                fact=f,
                sim=sim, rec=rec, lex=lex, score=final,
                answer_text=self._extract_a(f.text),
                question_text=self._fact_q[fid],
                aliases=self._fact_aliases[fid],
                category=self._extract_cat(f.text)
            ))

        out.sort(key=lambda x: -x.score)
        return out[:k]

    def answer(self, query: str, now_ts: Optional[float] = None, k: int = 5) -> dict:
        cands = self.retrieve(query, now_ts=now_ts, k=k)
        if not cands:
            return {"answer": "Nie mam odpowiedzi w pamięci.", "candidates": []}

        # Bezpieczeństwo: jeśli i dense i lexical są słabe → zwróć brak pewności
        if cands[0].sim < self.min_sim and cands[0].lex < 0.12:
            return {
                "answer": "Nie mam pewnej odpowiedzi w pamięci. Spróbuj doprecyzować pytanie.",
                "candidates": [{
                    "preview": c.fact.text.splitlines()[:2],
                    "score": round(c.score, 3),
                    "sim": round(c.sim, 3),
                    "lex": round(c.lex, 3),
                    "recency": round(c.rec, 3),
                    "category": c.category,
                    "question": c.question_text,
                    "aliases": c.aliases
                } for c in cands]
            }

        best = cands[0]
        return {
            "answer": best.answer_text,
            "category": best.category,
            "matched_question": best.question_text,
            "score": round(best.score, 3),
            "sim": round(best.sim, 3),
            "lex": round(best.lex, 3),
            "recency": round(best.rec, 3),
            "alternatives": [{
                "answer": c.answer_text,
                "category": c.category,
                "question": c.question_text,
                "score": round(c.score, 3)
            } for c in cands[1:3]]
        }

# Fabryka: buduje bota z pliku FAQ
def build_bot_from_faq(faq_path: str, alpha: float = 0.7, min_sim: float = 0.5,
                       lex_weight: float = 0.4, strict_alias_boost: float = 0.25) -> MemoryQABot:
    from adapters.faq_ingest_adapter import ingest_faq_to_graph
    gm = GraphMem()
    ingest_faq_to_graph(faq_path, gm)
    return MemoryQABot(gm, alpha=alpha, min_sim=min_sim,
                       lex_weight=lex_weight, strict_alias_boost=strict_alias_boost)
