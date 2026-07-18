#!/usr/bin/env python3
"""
FSOT explanatory layer — content before tissue.

Problem we fix:
  Occupation + fluent arcs are coherent but can say nothing.
  Real explanation needs killable claims first, then optional organ seal.

  python scripts/fsot_explain.py --once "why are free parameters the wrong architecture?"
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
PACK = DATA / "explanatory_pack.json"

ROLE_ORDER = ("definition", "mechanism", "contrast", "why", "seal")
ROLE_LABEL = {
    "definition": "What it is",
    "mechanism": "How it works",
    "contrast": "What it is not / contrast",
    "why": "Why it matters",
    "seal": "Close",
}


def load_pack(path: Path | None = None) -> dict:
    p = path or PACK
    if not p.exists():
        return {"topics": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _tokset(text: str) -> set[str]:
    return {t for t in re.split(r"\W+", (text or "").lower()) if len(t) >= 2}


def score_topic(topic: dict, query: str) -> float:
    q = (query or "").lower()
    qtoks = _tokset(q)
    score = 0.0
    for cue in topic.get("cues") or []:
        c = cue.lower()
        if c in q:
            # multi-word cue hits hard
            score += 3.0 + 0.4 * c.count(" ")
        else:
            # partial token overlap on cue words
            ctoks = _tokset(c)
            if ctoks and ctoks <= qtoks:
                score += 1.5
            elif ctoks & qtoks:
                score += 0.6 * len(ctoks & qtoks)
    # title tokens
    score += 0.35 * len(_tokset(topic.get("title") or "") & qtoks)
    # claim body soft match
    for cl in topic.get("claims") or []:
        overlap = len(_tokset(cl.get("text") or "") & qtoks)
        if overlap >= 2:
            score += 0.15 * min(overlap, 6)
    return score


def retrieve_topics(query: str, pack: dict | None = None, top_k: int = 2) -> list[tuple[float, dict]]:
    pack = pack or load_pack()
    scored = []
    for t in pack.get("topics") or []:
        s = score_topic(t, query)
        if s > 0:
            scored.append((s, t))
    scored.sort(key=lambda x: -x[0])
    return scored[: max(1, top_k)]


def pick_claims(topic: dict, depth: str = "turn") -> list[dict]:
    """
    depth:
      brief  — definition + seal if any
      turn   — definition, one mechanism, why, seal
      deep   — all roles present, multiple mechanisms
    """
    by_role: dict[str, list[dict]] = {}
    for c in topic.get("claims") or []:
        by_role.setdefault(c.get("role") or "mechanism", []).append(c)

    out: list[dict] = []

    def take(role: str, n: int) -> None:
        for c in (by_role.get(role) or [])[:n]:
            out.append(c)

    if depth == "brief":
        take("definition", 1)
        take("seal", 1)
        if not out:
            take("mechanism", 1)
        return out

    if depth == "deep":
        take("definition", 2)
        take("mechanism", 3)
        take("contrast", 1)
        take("why", 1)
        take("seal", 1)
        return out

    # turn default
    take("definition", 1)
    take("mechanism", 2)
    take("contrast", 1)
    take("why", 1)
    take("seal", 1)
    return out


def compose_explanation(
    query: str,
    *,
    depth: str = "turn",
    pack: dict | None = None,
    max_topics: int = 2,
) -> dict:
    """
    Build a multi-paragraph explanation from claim bank.
    Returns structured doc + plain reply text.
    """
    pack = pack or load_pack()
    hits = retrieve_topics(query, pack, top_k=max_topics if depth == "deep" else 1)
    if not hits or hits[0][0] < 0.8:
        # fallback generic spine
        generic = {
            "id": "fallback_fsot",
            "title": "FSOT reading",
            "domain": "linguistic",
            "claims": [
                {
                    "role": "definition",
                    "text": (
                        "FSOT explanations start from seeds {π, e, φ, γ, G} and scalar "
                        "S = K(T1+T2+T3), then land in a domain organ (D_eff folds)."
                    ),
                },
                {
                    "role": "mechanism",
                    "text": (
                        "Routing chooses an organ; occupation scores local candidates; "
                        "fluent surface is optional tissue over those anchors."
                    ),
                },
                {
                    "role": "why",
                    "text": (
                        "Without a claim layer, answers can sound coherent and still teach nothing. "
                        "Substance requires definitions and mechanisms that could be false."
                    ),
                },
                {
                    "role": "seal",
                    "text": (
                        f"I do not yet have a dense claim pack for “{query[:80]}”. "
                        "Ask about free parameters, domain occupation, scalar S, collapse, "
                        "PFLT, medical routing, learning η, or authority — or store a fact with remember."
                    ),
                },
            ],
        }
        hits = [(0.5, generic)]

    sections = []
    reply_parts = []
    primary_domain = hits[0][1].get("domain") or "linguistic"

    # Direct lead: answer in one breath from first definition
    first_claims = pick_claims(hits[0][1], depth=depth)
    first_def = next((c for c in first_claims if c.get("role") == "definition"), first_claims[0] if first_claims else None)
    if first_def:
        lead = first_def["text"]
        reply_parts.append(lead)
        sections.append({"kind": "lead", "text": lead, "topic": hits[0][1].get("id")})

    for rank, (score, topic) in enumerate(hits):
        claims = pick_claims(topic, depth=depth)
        # skip lead definition already used for primary
        if rank == 0 and first_def:
            claims = [c for c in claims if c is not first_def]

        title = topic.get("title") or topic.get("id")
        if rank > 0 or depth == "deep":
            hdr = f"**{title}**"
            reply_parts.append(hdr)
            sections.append({"kind": "heading", "text": title, "score": score})

        prev_role = None
        for c in claims:
            role = c.get("role") or "mechanism"
            text = (c.get("text") or "").strip()
            if not text:
                continue
            # discourse glue between real claims (not empty occupation)
            if prev_role and role != prev_role:
                glue = {
                    ("definition", "mechanism"): "Here is the mechanism.",
                    ("mechanism", "mechanism"): "Further:",
                    ("mechanism", "contrast"): "By contrast:",
                    ("definition", "contrast"): "By contrast:",
                    ("mechanism", "why"): "Why this matters:",
                    ("contrast", "why"): "Why this matters:",
                    ("why", "seal"): "So:",
                    ("mechanism", "seal"): "So:",
                    ("definition", "seal"): "So:",
                    ("contrast", "seal"): "So:",
                }.get((prev_role, role), "")
                if glue and depth != "brief":
                    reply_parts.append(glue)
                    sections.append({"kind": "glue", "text": glue})
            # Plain prose (labels are for structure, not "What it is: What it is:" clutter)
            reply_parts.append(text)
            sections.append(
                {
                    "kind": "claim",
                    "role": role,
                    "text": text,
                    "topic": topic.get("id"),
                    "score": score,
                }
            )
            prev_role = role

    reply = " ".join(reply_parts)
    # mild cleanup
    reply = re.sub(r"\s+", " ", reply).strip()
    reply = re.sub(r"\s+\*\*", " **", reply)

    return {
        "query": query,
        "mode": f"explain_{depth}",
        "domain": primary_domain,
        "topics": [
            {"id": t.get("id"), "title": t.get("title"), "score": s, "domain": t.get("domain")}
            for s, t in hits
        ],
        "sections": sections,
        "reply": reply,
        "n_claims": sum(1 for s in sections if s.get("kind") == "claim"),
        "formula": (
            "explain = retrieve(claim_bank, query) → ordered roles "
            "(definition→mechanism→contrast→why→seal) + discourse glue; "
            "optional organ seal outside this module"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", type=str, default="")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--brief", action="store_true")
    args = ap.parse_args()
    depth = "deep" if args.deep else ("brief" if args.brief else "turn")
    q = args.once or "why are free parameters the wrong architecture for FSOT?"
    doc = compose_explanation(q, depth=depth)
    print(doc["reply"])
    print(f"\n[{doc['mode']}|{doc['domain']}|claims={doc['n_claims']}|topics={[t['id'] for t in doc['topics']]}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
