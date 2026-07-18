#!/usr/bin/env python3
"""
Boot and run the FSOT LLM (Python parity of Mathematica FSOTLLM.wl).

Fix (domain allocation + D_eff):
  Embeddings and next-token candidates are NOT a flat soup.
  Each domain has folds (D_eff, delta_psi, observed). Tokens are allocated to
  domains from the curriculum. Embeddings are evaluated on that domain's D_eff
  spine so pieces connect through the scalar field the way PFLT/Lean route them.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
MEM = HOME / "memory"
TRACES = HOME / "llm" / "traces"
AUTH = DATA / "fsot_seeds_authority.json"
CUR = DATA / "fsot_llm_curriculum.json"
VOCAB = DATA / "fsot_llm_vocab.json"
MODEL_OUT = MEM / "fsot_llm_model.json"
TRACE_OUT = TRACES / "last_forward_trace.json"
RUN_REPORT = DATA / "fsot_llm_run_report.json"

# ---- seeds / layer-1/2 (archive + GPU) ----
PI = math.pi
E = math.e
PHI = (1 + math.sqrt(5)) / 2
GAMMA = 0.5772156649015329
G_CAT = 0.9159655941772190
ALPHA = math.log(PI) / (E * PHI**13)
PSI_CON = 1 - math.exp(-1)
ETA_EFF = 1 / (PI - 1)
BETA = math.exp(-(PI**PI + (E - 1)))
GAMMA_C = -math.log(2) / PHI
OMEGA = math.sin(PI / E) * math.sqrt(2)
THETA_S = math.sin(PSI_CON * ETA_EFF)
POOF = math.exp((-math.log(PI) / E) / (ETA_EFF * math.log(PHI)))
C_EFF = (1 - POOF * math.sin(THETA_S)) * (1 + 0.01 * G_CAT / (PI * PHI))
A_BLEED = math.sin(PI / E) * PHI / math.sqrt(2)
P_VAR = -math.cos(THETA_S + PI)
B_IN = C_EFF * (1 - math.sin(THETA_S) / PHI)
A_IN = A_BLEED * (1 + math.cos(THETA_S) / PHI)
SUCTION = POOF * (-math.cos(THETA_S - PI))
CHAOS = GAMMA_C / OMEGA
P_NEW = (GAMMA / E) * math.sqrt(2)
C_FACTOR = C_EFF * P_NEW
K = PHI * (GAMMA / E) * math.sqrt(2) / math.log(PI) * 0.99
COLLAPSE = C_EFF * P_VAR

# Domain allocation table — same routing idea as PFLT / Lean get_domain_params
DOMAIN_FOLDS = {
    "linguistic": {"D_eff": 16.0, "delta_psi": 0.8, "observed": True},
    "cosmological": {"D_eff": 25.0, "delta_psi": 1.0, "observed": False},
    "quantum": {"D_eff": 6.0, "delta_psi": 1.0, "observed": True},
    "neural": {"D_eff": 14.0, "delta_psi": 0.7, "observed": True},
    "chemical": {"D_eff": 9.0, "delta_psi": 0.5, "observed": True},
    "biological": {"D_eff": 12.0, "delta_psi": 0.08, "observed": False},
    "consciousness": {"D_eff": 16.0, "delta_psi": 1.15, "observed": True},
    "mythological": {"D_eff": 21.0, "delta_psi": 1.0, "observed": True},
    "genomic": {"D_eff": 12.0, "delta_psi": 0.5, "observed": False},
    "medical": {"D_eff": 13.0, "delta_psi": 0.35, "observed": True},
}

# Structured decode: 6–8 role short "sentences" per organ (occupation order, not free beam)
# Roles share the same scorer; D_eff regime + prefer lists differ by domain.
DOMAIN_SLOTS = {
    "linguistic": [
        {"role": "subject", "prefer": ["fsot", "fluid", "proto", "language", "universal"]},
        {"role": "link", "prefer": ["field", "domain", "structure", "phase"]},
        {"role": "act", "prefer": ["translate", "communicate", "verify", "observe"]},
        {"role": "object", "prefer": ["meaning", "language", "seed", "scalar"]},
        {"role": "qual", "prefer": ["structure", "consensus", "parameter", "formula"]},
        {"role": "bridge", "prefer": ["spacetime", "fluid", "theory", "omni"]},
        {"role": "close", "prefer": ["truth", "proof", "theory", "verify"]},
        {"role": "seal", "prefer": ["fsot", "seed", "consensus", "parameter"]},
    ],
    "quantum": [
        {"role": "subject", "prefer": ["quantum", "particle", "nuclear", "field"]},
        {"role": "link", "prefer": ["phase", "structure", "field", "measure"]},
        {"role": "act", "prefer": ["collapse", "measure", "observe"]},
        {"role": "state", "prefer": ["trinary", "superposed", "structure"]},
        {"role": "qual", "prefer": ["coherence", "consensus", "phase"]},
        {"role": "object", "prefer": ["measure", "field", "seed"]},
        {"role": "close", "prefer": ["truth", "seed", "verify"]},
        {"role": "seal", "prefer": ["trinary", "consensus", "quantum"]},
    ],
    "medical": [
        {"role": "subject", "prefer": ["medical", "medicine", "signal", "clinical"]},
        {"role": "link", "prefer": ["field", "structure", "signal", "phase"]},
        {"role": "act", "prefer": ["diagnose", "measure", "observe", "verify"]},
        {"role": "object", "prefer": ["truth", "signal", "life", "structure"]},
        {"role": "qual", "prefer": ["parameter", "measure", "field"]},
        {"role": "bridge", "prefer": ["consciousness", "neural", "code"]},
        {"role": "close", "prefer": ["verify", "truth", "diagnose"]},
        {"role": "seal", "prefer": ["medical", "signal", "field"]},
    ],
    "neural": [
        {"role": "subject", "prefer": ["neural", "mind", "consciousness", "neuroscience"]},
        {"role": "link", "prefer": ["field", "phase", "structure"]},
        {"role": "act", "prefer": ["observe", "measure", "communicate"]},
        {"role": "object", "prefer": ["consciousness", "mind", "field", "structure"]},
        {"role": "qual", "prefer": ["consensus", "coherence", "phase"]},
        {"role": "bridge", "prefer": ["signal", "language", "meaning"]},
        {"role": "close", "prefer": ["truth", "seed", "observe"]},
        {"role": "seal", "prefer": ["consciousness", "neural", "consensus"]},
    ],
    "mythological": [
        {"role": "subject", "prefer": ["sky", "earth", "water", "time", "king"]},
        {"role": "link", "prefer": ["field", "form", "flow", "phase"]},
        {"role": "act", "prefer": ["create", "form", "flow", "measure"]},
        {"role": "object", "prefer": ["form", "law", "god", "water", "tablet"]},
        {"role": "qual", "prefer": ["judgment", "structure", "life"]},
        {"role": "bridge", "prefer": ["language", "meaning", "truth"]},
        {"role": "close", "prefer": ["truth", "life", "form"]},
        {"role": "seal", "prefer": ["earth", "sky", "create"]},
    ],
    "cosmological": [
        {"role": "subject", "prefer": ["spacetime", "cosmology", "astronomy", "field"]},
        {"role": "link", "prefer": ["phase", "scalar", "structure", "flow"]},
        {"role": "act", "prefer": ["flow", "measure", "observe"]},
        {"role": "object", "prefer": ["seed", "scalar", "phase", "structure"]},
        {"role": "qual", "prefer": ["pi", "phi", "catalan", "parameter"]},
        {"role": "bridge", "prefer": ["quantum", "field", "energy"]},
        {"role": "close", "prefer": ["truth", "seed", "verify"]},
        {"role": "seal", "prefer": ["spacetime", "scalar", "phi"]},
    ],
    "chemical": [
        {"role": "subject", "prefer": ["chemical", "chemistry", "structure", "energy"]},
        {"role": "link", "prefer": ["field", "phase", "code", "bond"]},
        {"role": "act", "prefer": ["start", "transfer", "measure", "create"]},
        {"role": "object", "prefer": ["code", "structure", "energy", "field"]},
        {"role": "qual", "prefer": ["parameter", "measure", "phase"]},
        {"role": "bridge", "prefer": ["biological", "quantum", "seed"]},
        {"role": "close", "prefer": ["truth", "verify", "seed"]},
        {"role": "seal", "prefer": ["structure", "energy", "code"]},
    ],
    "genomic": [
        {"role": "subject", "prefer": ["codon", "genetics", "code", "start"]},
        {"role": "link", "prefer": ["structure", "sequence", "field", "phase"]},
        {"role": "act", "prefer": ["transfer", "start", "action", "measure"]},
        {"role": "object", "prefer": ["code", "structure", "energy", "codon"]},
        {"role": "qual", "prefer": ["life", "parameter", "verify"]},
        {"role": "bridge", "prefer": ["biological", "chemical", "signal"]},
        {"role": "close", "prefer": ["action", "life", "verify"]},
        {"role": "seal", "prefer": ["codon", "transfer", "start"]},
    ],
    "biological": [
        {"role": "subject", "prefer": ["biology", "life", "biochemistry", "structure"]},
        {"role": "link", "prefer": ["field", "code", "phase", "form"]},
        {"role": "act", "prefer": ["transfer", "observe", "create", "measure"]},
        {"role": "object", "prefer": ["life", "code", "structure", "species"]},
        {"role": "qual", "prefer": ["form", "parameter", "field"]},
        {"role": "bridge", "prefer": ["genomic", "chemical", "medical"]},
        {"role": "close", "prefer": ["life", "truth", "form"]},
        {"role": "seal", "prefer": ["life", "biology", "structure"]},
    ],
    "consciousness": [
        {"role": "subject", "prefer": ["consciousness", "mind", "observe", "psychology"]},
        {"role": "link", "prefer": ["field", "phase", "structure", "signal"]},
        {"role": "act", "prefer": ["observe", "measure", "communicate", "verify"]},
        {"role": "object", "prefer": ["truth", "field", "mind", "structure"]},
        {"role": "qual", "prefer": ["consensus", "coherence", "parameter"]},
        {"role": "bridge", "prefer": ["neural", "language", "meaning"]},
        {"role": "close", "prefer": ["truth", "seed", "observe"]},
        {"role": "seal", "prefer": ["consciousness", "mind", "consensus"]},
    ],
}


def load_domain_slots() -> dict:
    """Merge static DOMAIN_SLOTS with data/domain_slot_prefers.json (PFLT gold)."""
    path = DATA / "domain_slot_prefers.json"
    slots = {k: [dict(s) for s in v] for k, v in DOMAIN_SLOTS.items()}
    if not path.exists():
        return slots
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return slots
    for dom, info in (doc.get("domains") or {}).items():
        roles = info.get("roles") or []
        if not roles:
            continue
        # replace or extend
        merged = []
        by_role = {r["role"]: list(r.get("prefer") or []) for r in roles}
        base = slots.get(dom) or slots.get("linguistic") or []
        base_roles = {s["role"]: list(s.get("prefer") or []) for s in base}
        all_roles = list(dict.fromkeys(list(base_roles.keys()) + list(by_role.keys())))
        for role in all_roles:
            pref = []
            for x in (by_role.get(role) or []) + (base_roles.get(role) or []):
                if x not in pref:
                    pref.append(x)
            merged.append({"role": role, "prefer": pref[:14]})
        slots[dom] = merged
    return slots


# Universal bridge tokens always eligible (connect domains)
SEED_CORE = {
    "fsot", "fluid", "spacetime", "seed", "scalar", "domain", "structure",
    "energy", "field", "phase", "flow", "translate", "communicate", "language",
    "meaning", "observe", "collapse", "trinary", "consensus", "proof", "truth",
    "measure", "verify", "parameter", "theory", "omni", "universal", "proto",
    "diagnose", "medical", "mind", "consciousness", "form", "create", "action",
    "start", "transfer", "code", "therefore", "cause", "effect",
    "pi", "phi", "euler", "catalan",
    # mythological content (water/king/…) lives in domain prefers, not global SEED_CORE
}
STOPWORDS = {"the", "a", "an", "of", "and", "to", "in", "is", "that", "for", "on", "with", "as", "by", "or"}
UNIVERSAL = {
    "fsot", "fluid", "spacetime", "seed", "scalar", "domain", "structure",
    "energy", "field", "phase", "flow", "translate", "communicate", "language",
    "meaning", "observe", "collapse", "trinary", "consensus", "proof", "truth",
    "measure", "verify", "zero", "parameter", "theory", "omni",
}

# Closed surface lexicon for fluent assembly (not free parameters — fixed realization)
# Path to GPT-class readability: skeleton occupation stays FSOT; surface English varies by Φ-index.
FLUENT_FUNCTION = {
    "the", "a", "an", "of", "and", "to", "in", "is", "that", "for", "on", "with",
    "as", "by", "or", "into", "from", "through", "across", "under", "over", "its",
    "this", "these", "those", "same", "such", "also", "then", "so", "when", "where",
    "which", "whose", "without", "within", "between", "among", "upon", "about",
}


def _phi_pick(options: list[str], i: int, salt: int = 0) -> str:
    if not options:
        return ""
    return options[int((i + 1) * PHI * 3 + salt) % len(options)]


# Acts that may safely take English -s morphology; others remap to a real verb.
_VERB_ACTS = {
    "do", "be", "have", "go", "observe", "collapse", "measure", "verify",
    "translate", "communicate", "create", "diagnose", "flow", "start",
    "transfer", "seed", "form", "prove", "hold", "join", "map", "route",
    "occupy", "carry", "shape", "bind", "read", "write", "speak", "mean",
    "interact", "emerge", "seal", "open", "close", "guide", "show", "move",
    "connect", "link", "fold", "align", "check", "confirm", "return",
}


def verb_s(act: str) -> str:
    """Minimal present-tense surface for slot verbs (closed morphology)."""
    a = (act or "move").lower()
    # Non-verbs that often land in act slots → remap (occupation token, surface verb)
    nounish = {
        "fsot": "carries",
        "fluid": "flows",
        "language": "expresses",
        "domain": "occupies",
        "scalar": "modulates",
        "seed": "grounds",
        "field": "extends",
        "structure": "shapes",
        "phase": "shifts",
        "mind": "holds",
        "consciousness": "registers",
        "quantum": "collapses",
        "truth": "grounds",
        "theory": "frames",
        "parameter": "sets",
        "code": "encodes",
        "energy": "drives",
        "spacetime": "curves",
        "proto": "begins",
        "omni": "spans",
        "consensus": "aligns",
        "proof": "confirms",
        "meaning": "signifies",
        "trinary": "resolves",
        "therefore": "implies",
        "cause": "drives",
        "effect": "yields",
        "medical": "diagnoses",
        "neural": "fires",
        "measure": "measures",
    }
    if a in nounish:
        return nounish[a]
    irregular = {
        "do": "does",
        "be": "is",
        "have": "has",
        "go": "goes",
        "observe": "observes",
        "collapse": "collapses",
        "measure": "measures",
        "verify": "verifies",
        "translate": "translates",
        "communicate": "communicates",
        "create": "creates",
        "diagnose": "diagnoses",
        "flow": "flows",
        "start": "starts",
        "transfer": "transfers",
        "seed": "seeds",
        "form": "forms",
        "prove": "proves",
        "hold": "holds",
        "join": "joins",
        "map": "maps",
        "route": "routes",
        "occupy": "occupies",
        "carry": "carries",
        "shape": "shapes",
        "bind": "binds",
        "read": "reads",
        "write": "writes",
        "speak": "speaks",
        "mean": "means",
        "interact": "interacts",
        "emerge": "emerges",
        "connect": "connects",
        "align": "aligns",
        "confirm": "confirms",
    }
    if a in irregular:
        return irregular[a]
    if a not in _VERB_ACTS and a not in irregular:
        # Unknown occupation token: do not invent "fsots" — use carrier verb
        return "carries"
    if a.endswith(("s", "x", "z", "ch", "sh")):
        return a + "es"
    if a.endswith("y") and len(a) > 1 and a[-2] not in "aeiou":
        return a[:-1] + "ies"
    return a + "s"


def assemble_fluent(
    roles: dict[str, str],
    *,
    phase: str = "structure",
    domain: str = "linguistic",
    index: int = 0,
    topic: str | None = None,
) -> str:
    """
    Natural English realization of an occupied role map.

    Content tokens stay domain-scored occupation; word order + glue templates
    are Φ-indexed closed surfaces (path toward GPT fluency without free ranking).
    """
    sub = roles.get("subject") or roles.get("seal") or "field"
    link = roles.get("link") or "field"
    act = roles.get("act") or "observe"
    obj = roles.get("object") or roles.get("state") or "structure"
    qual = roles.get("qual") or "structure"
    bridge = roles.get("bridge") or "domain"
    close = roles.get("close") or "truth"
    seal = roles.get("seal") or "seed"
    vs = verb_s(act)
    # Phase-tinted openings (discourse, not free style models)
    openers = {
        "emergence": [
            f"At first, {sub} {vs} the {obj}",
            f"Out of the {link}, {sub} {vs} {obj}",
            f"When the {domain} fold opens, {sub} {vs} the {obj}",
            f"{sub.capitalize()} begins as it {vs} the {obj}",
        ],
        "structure": [
            f"In the {link}, {sub} {vs} the {obj}",
            f"Structurally, {sub} {vs} {obj} through {bridge}",
            f"Inside this {link}, {sub} {vs} the {obj} with {qual}",
            f"The {sub} of the {link} {vs} {obj}",
        ],
        "interaction": [
            f"As it meets {bridge}, {sub} {vs} the {obj}",
            f"Through {bridge}, {sub} {vs} {obj} into {close}",
            f"{sub.capitalize()} interacts as it {vs} the {obj} via {bridge}",
            f"Across the {bridge}, {sub} {vs} {obj}",
        ],
        "measure": [
            f"Under measure, {sub} {vs} the {obj}",
            f"Observation shows that {sub} {vs} {obj} with {qual}",
            f"When measured, {sub} {vs} the {obj} toward {close}",
            f"{sub.capitalize()} {vs} {obj} as a measurable {qual}",
        ],
        "seal": [
            f"Finally, {sub} {vs} the {obj} toward {seal}",
            f"This seals as {sub} {vs} {obj} into {close}",
            f"In closing, {sub} {vs} the {obj} — {seal}",
            f"The path settles when {sub} {vs} {obj} at {seal}",
        ],
        "coherence": [
            f"Holding together, {sub} {vs} the {obj} with {qual}",
            f"Consensus forms as {sub} {vs} {obj} through {bridge}",
        ],
        "verification": [
            f"Checked against seed, {sub} {vs} the {obj} toward {close}",
            f"Verification has {sub} {vs} {obj} with {qual}",
        ],
    }
    bank = openers.get(phase) or openers["structure"]
    core = _phi_pick(bank, index, salt=len(sub) + len(act))
    # Mid / close clauses (Φ-selected, closed)
    mids = [
        f" with {qual}",
        f" through the {bridge}",
        f" under {qual}",
        f", guided by {bridge}",
        f" in light of {qual}",
        "",
    ]
    ends = [
        f", toward {close}",
        f" — and the seal is {seal}",
        f", aiming at {close}",
        f". That points to {seal}",
        f", settling on {seal}",
        f" into {close}",
    ]
    # Avoid double-including pieces already in core
    mid = _phi_pick(mids, index, salt=2)
    end = _phi_pick(ends, index, salt=5)
    core_l = core.lower()
    # Drop mid/end if any content word already appears in prior text (anti-echo)
    def _echoes(frag: str, prior: str) -> bool:
        words = [w for w in re.findall(r"[a-z0-9]+", frag.lower()) if len(w) > 3]
        if not words:
            return False
        return any(w in prior for w in words)

    if mid and _echoes(mid, core_l):
        mid = ""
    prior = (core + mid).lower()
    if end and _echoes(end, prior):
        end = f" — {seal}."
    if topic and topic not in core_l and index % 3 == 0:
        core = f"On {topic}, " + core[0].lower() + core[1:]
    text = (core + mid + end).strip()
    # cleanup spaces / punctuation / doubled prepositions / doubled content words
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.—])", r"\1", text)
    text = re.sub(r"([.]){2,}", r".", text)
    text = re.sub(r"\b(with|toward|through|into|under)\s+\1\b", r"\1", text, flags=re.I)
    text = re.sub(r"\b(\w{4,})\s+\1\b", r"\1", text, flags=re.I)
    # "with X under X" / "under X into X"
    text = re.sub(
        r"\b(with|under|through|into|toward)\s+(\w{3,})\s+(with|under|through|into|toward)\s+\2\b",
        r"\1 \2",
        text,
        flags=re.I,
    )
    if not text.endswith("."):
        text += "."
    # Capitalize first letter if needed
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def assemble_fluent_connector(
    phase: str, a: str, b: str, c: str, index: int = 0
) -> str:
    """Natural logical glue — still fixed templates + seed fills."""
    templates = {
        "consequence": [
            f"Therefore {a} joins {b} toward {c}",
            f"So {a} carries {b} into {c}",
            f"From that, {a} binds {b} to {c}",
            f"As a result, {a} and {b} move toward {c}",
        ],
        "coherence": [
            f"Thus {a} and {b} hold consensus in the field of {c}",
            f"In other words, {a} and {b} cohere around {c}",
            f"So the same field keeps {a} with {b} at {c}",
            f"Thus {a} stays aligned with {b} through {c}",
        ],
        "verification": [
            f"Hence {a} verifies {b} against seed {c}",
            f"Checked that way, {a} confirms {b} under {c}",
            f"Hence the measure of {a} against {b} returns {c}",
            f"So verification reads {a} with {b} as {c}",
        ],
        "transition": [
            f"As above, so below: {a} maps into {b} via {c}",
            f"The same pattern sends {a} into {b} through {c}",
        ],
    }
    bank = templates.get(phase) or templates["consequence"]
    raw = _phi_pick(bank, index, salt=len(a) + len(b))
    text = raw[0].upper() + raw[1:] + "."
    return text


# Closed bridge phrases (surface only) — free-gen fills open class between anchors
BRIDGE_PHRASES = [
    "in the field of",
    "by way of",
    "under the law of",
    "through the medium of",
    "as it meets",
    "along the path of",
    "inside the fold of",
    "across the domain of",
    "with respect to",
    "in light of",
    "on the spine of",
    "toward the seal of",
    "from the seed of",
    "into the measure of",
    "against the proof of",
    "within the structure of",
    "under observation of",
    "as consensus around",
]


def bridge_phrase(index: int, salt: int = 0) -> str:
    return _phi_pick(BRIDGE_PHRASES, index, salt=salt)


def raw_s(
    D_eff=25.0,
    delta_psi=1.0,
    delta_theta=1.0,
    recent_hits=0.0,
    observed=False,
    N=1.0,
    P=1.0,
    rho=1.0,
) -> float:
    growth = math.exp(ALPHA * (1 - recent_hits / N) * GAMMA / PHI)
    base = (
        (N * P / math.sqrt(D_eff))
        * math.cos((PSI_CON + delta_psi) / ETA_EFF)
        * math.exp(-ALPHA * recent_hits / N + rho + B_IN * delta_psi)
        * (1 + growth * C_EFF)
    )
    t1 = base * (1 + P_NEW * math.log(max(D_eff, 1e-9) / 25.0))
    if observed:
        t1 *= math.exp(C_FACTOR * P_VAR) * math.cos(delta_psi + P_VAR)
    t2 = 1.0
    valve = (
        BETA
        * math.cos(delta_psi)
        * (N * P / math.sqrt(D_eff))
        * (1 + CHAOS * (D_eff - 25.0) / 25.0)
        * (1 + POOF * math.cos(THETA_S + PI) + SUCTION * math.sin(THETA_S))
    )
    acoustic = (
        1
        + (A_BLEED * math.sin(delta_theta) ** 2) / PHI
        + (A_IN * math.cos(delta_theta) ** 2) / PHI
    )
    phase = 1 + B_IN * P_VAR
    t3 = valve * acoustic * phase
    return K * (t1 + t2 + t3)


def token_unit(s: str) -> float:
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:12], 16) / float(16**12)


def field_scale(dim: int = 32) -> float:
    return PHI / (abs(COLLAPSE) * max(math.sqrt(1.0 / dim), 1e-9))


def embed_token_domain(tok: str, dim: int, folds: dict) -> list[float]:
    """
    Domain-allocated embedding.

    The compactification ladder is ANCHORED at the domain's D_eff — not a free
    global ladder. Pieces connect: token mass (u) × domain D_eff spine × δψ.
    """
    u = token_unit(tok)
    D0 = float(folds["D_eff"])
    dp0 = float(folds["delta_psi"])
    obs = bool(folds["observed"])
    vec = []
    for i in range(dim):
        # Spine around domain D_eff: connect neighboring compactification rungs
        # offset spans ~±D0/4 so quantum (6) and cosmo (25) stay distinct regimes
        offset = ((i + 0.5) / dim - 0.5) * (D0 / 2.0)
        d_eff = max(3.0, min(25.0, D0 + offset + 0.5 * u))
        # Domain δψ with token micro-phase (allocation, not free param)
        delta_psi = max(0.05, min(2.5, dp0 * (0.75 + 0.5 * u)))
        delta_theta = (u + i / max(dim, 1)) * (PI / E)  # seed angle
        s = raw_s(
            D_eff=d_eff,
            delta_psi=delta_psi,
            delta_theta=delta_theta,
            recent_hits=float(i % 3) * u,
            observed=obs if i % 2 == 0 else (not obs and u > 0.5),
        )
        # Domain tag in the last geometric degrees of freedom: 1/sqrt(D_eff) factor
        s = s * (1.0 + 0.2 * math.sin(2 * math.pi * u * PHI * (i + 1)))
        vec.append(s)
    nrm = math.sqrt(sum(x * x for x in vec)) or 1e-12
    return [x / nrm for x in vec]


def collapse(x: float, scale: float = 1.0) -> int:
    y = x * scale
    if y > COLLAPSE:
        return 2
    if y < -COLLAPSE:
        return 0
    return 1


def coherence(row: list[float], scale: float | None = None) -> float:
    sc = scale if scale is not None else field_scale(len(row) or 32)
    codes = [collapse(x, sc) for x in row]
    sharp = sum(1 for c in codes if c != 1)
    return sharp / max(len(codes), 1)


def cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-12
    nb = math.sqrt(sum(x * x for x in b)) or 1e-12
    return num / (na * nb)


def trit_sim(a: list[float], b: list[float]) -> float:
    sc = field_scale(len(a) or 32)
    ca = [collapse(x, sc) for x in a]
    cb = [collapse(x, sc) for x in b]
    n = min(len(ca), len(cb))
    if n == 0:
        return 0.0
    acc = 0
    for i in range(n):
        ta, tb = ca[i], cb[i]
        if ta == 1 or tb == 1:
            continue
        acc += 1 if ta == tb else -1
    return acc / n


def hybrid_score(a: list[float], b: list[float]) -> float:
    return 0.55 * cosine(a, b) + 0.45 * trit_sim(a, b)


def phase_rotate(mat: list[list[float]]) -> list[list[float]]:
    out = [row[:] for row in mat]
    for i, row in enumerate(out):
        theta = 2.0 * i
        cs, sn = math.cos(theta), math.sin(theta)
        dim = len(row)
        for k in range(dim // 2):
            a, b = row[2 * k], row[2 * k + 1]
            row[2 * k] = cs * a - sn * b
            row[2 * k + 1] = sn * a + cs * b
    return out


def consensus(q, k, v):
    seq = len(q)
    sim = [[trit_sim(q[i], k[j]) for j in range(seq)] for i in range(seq)]
    coh = [coherence(k[j]) for j in range(seq)]
    gate = [
        [sim[i][j] if (j <= i and coh[j] > 0.5) else 0.0 for j in range(seq)]
        for i in range(seq)
    ]
    out = []
    for i in range(seq):
        active = max(sum(1 for j in range(seq) if gate[i][j] != 0.0), 1.0)
        dim = len(v[0])
        acc = [0.0] * dim
        for j in range(seq):
            w = gate[i][j]
            if w == 0.0:
                continue
            for d in range(dim):
                acc[d] += w * v[j][d]
        out.append([x / active for x in acc])
    return out, coh, sim


def ffn(mat):
    inv = 1 + 1 / PHI
    res = []
    for row in mat:
        r = [max(x, 0.0) for x in row]
        res.append([(row[i] + r[i] / PHI) / inv for i in range(len(row))])
    return res


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\W+", text.lower()) if t]


# Cue weights: more specific organs outrank shared vocabulary (e.g. spacetime vs language)
DOMAIN_CUES = {
    "medical": (3.0, ("medical", "diagnose", "clinical", "patient", "disease", "symptom", "therapy")),
    "genomic": (3.0, ("codon", "gene", "dna", "genome", "protein", "atg", "nucleotide")),
    "quantum": (3.0, ("quantum", "collapse", "particle", "higgs", "trinary", "superposed")),
    "cosmological": (2.5, ("cosmo", "galaxy", "hubble", "cmb", "cosmology", "universe")),
    "neural": (2.8, ("neural", "brain", "mind", "consciousness", "neuron", "cortex")),
    "chemical": (2.5, ("chemical", "molecule", "bond", "reaction", "atom")),
    "biological": (2.5, ("biology", "life", "species", "organism", "cell")),
    "mythological": (2.2, ("sky", "earth", "create", "sumer", "hieroglyph", "myth", "gods")),
    "consciousness": (2.0, ("observe", "living", "aware", "observer")),
    "linguistic": (3.2, ("translate", "language", "meaning", "word", "communicate", "proto", "fluid tongue", "lexicon", "gloss")),
}

# Shared cues that alone should not yank to cosmology when language is present
SOFT_CUES = {
    "spacetime": ("cosmological", 1.0),
    "space": ("cosmological", 0.4),
    "time": ("mythological", 0.3),
    "field": ("quantum", 0.3),
    "structure": ("linguistic", 0.2),
    "energy": ("chemical", 0.3),
    "fsot": ("linguistic", 0.5),
    "scalar": ("linguistic", 0.5),
    "seed": ("linguistic", 0.4),
    "domain": ("linguistic", 0.3),
}


def infer_domain(text: str, default: str = "linguistic") -> str:
    """Multi-cue occupation: highest weighted organ wins; language beats soft spacetime alone."""
    t = text.lower()
    scores = {d: 0.0 for d in DOMAIN_FOLDS}
    for dom, (w, keys) in DOMAIN_CUES.items():
        hits = sum(1 for k in keys if k in t)
        if hits:
            scores[dom] += w * hits
    for cue, (dom, w) in SOFT_CUES.items():
        if cue in t:
            scores[dom] += w
    # Disambiguation: language/communicate organ outranks cosmology if both fire lightly
    if scores["linguistic"] > 0 and scores["cosmological"] > 0:
        if any(k in t for k in ("language", "translate", "communicate", "meaning", "word", "proto")):
            scores["linguistic"] += 2.0
            scores["cosmological"] *= 0.5
    # "spacetime" alone without cosmo words stays milder
    if "spacetime" in t and not any(k in t for k in ("cosmo", "galaxy", "hubble", "cmb", "universe")):
        if scores["linguistic"] > 0 or scores["neural"] > 0:
            scores["cosmological"] *= 0.35
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] <= 0:
        return default
    return best[0]


def is_noise_token(tok: str) -> bool:
    """Diet filter: same numeric space can host junk; reject for linguistic occupation."""
    if not tok or tok.startswith("<"):
        return True
    if tok in UNIVERSAL:
        return False
    if len(tok) < 2:
        return True
    # classical / transliteration debris
    if tok.startswith(("a_", "an_", "the_")):
        return True
    if tok.count("_") > 2:
        return True
    # very rare short consonant piles
    if len(tok) <= 3 and not any(c in tok for c in "aeiou"):
        return True
    # place/name-ish latin dump markers (heuristic)
    if tok.endswith(("ium", "ius", "aea", "aea")) and len(tok) > 6:
        return True
    return False


class FSOTLLM:
    def __init__(self, dim: int = 32, vocab: list[str] | None = None):
        self.dim = dim
        self.vocab = vocab or ["<pad>", "<bos>", "<eos>", "<unk>", "fsot", "fluid"]
        self.domain = "linguistic"
        self.folds = dict(DOMAIN_FOLDS[self.domain])
        self.recent_hits = 0.0
        self.step = 0
        self.train_log: list[dict] = []
        self.last_trace: dict = {}
        # Domain allocation: token -> set of domains (occupation, not flat soup)
        self.token_domains: dict[str, set[str]] = defaultdict(set)
        # Frequency of token as TARGET in domain (diet ranking)
        self.token_freq: dict[tuple[str, str], int] = defaultdict(int)
        # Domain-keyed embeddings: (domain, token) -> vector
        self.emb: dict[tuple[str, str], list[float]] = {}
        # Cap linguistic organ size (local interaction set)
        self.max_cands = {
            "linguistic": 120,
            "mythological": 80,
            "medical": 80,
            "genomic": 80,
            "quantum": 60,
            "cosmological": 60,
            "neural": 60,
            "chemical": 60,
            "biological": 60,
            "consciousness": 60,
        }
        # Init universal tokens into every domain
        for tok in self.vocab:
            if tok in UNIVERSAL or tok in SEED_CORE or tok.startswith("<"):
                for d in DOMAIN_FOLDS:
                    self.token_domains[tok].add(d)
                    if tok in SEED_CORE:
                        self.token_freq[(d, tok)] += 5

    def set_domain(self, name: str) -> None:
        if name not in DOMAIN_FOLDS:
            name = "linguistic"
        self.domain = name
        self.folds = dict(DOMAIN_FOLDS[name])

    def allocate(self, tok: str, domain: str, *, as_target: bool = False) -> None:
        if is_noise_token(tok) and tok not in UNIVERSAL:
            return
        self.token_domains[tok].add(domain)
        if as_target:
            self.token_freq[(domain, tok)] += 1

    def embed_of(self, tok: str, domain: str | None = None) -> list[float]:
        dom = domain or self.domain
        key = (dom, tok)
        if key in self.emb:
            return self.emb[key]
        folds = DOMAIN_FOLDS.get(dom, self.folds)
        v = embed_token_domain(tok, self.dim, folds)
        self.emb[key] = v
        return v

    def candidates_for_domain(self, domain: str) -> list[str]:
        """
        Local occupation set for this organ (domain).
        Same numeric magnitudes can exist elsewhere; only this D_eff neighborhood votes.
        Linguistic diet is frequency-capped so the organ does not swallow the whole lexicon.
        """
        pool = []
        for tok, doms in self.token_domains.items():
            if tok.startswith("<") and tok not in ("<unk>",):
                continue
            if is_noise_token(tok) and tok not in UNIVERSAL:
                continue
            if domain in doms or tok in UNIVERSAL:
                freq = self.token_freq.get((domain, tok), 0)
                rank = freq
                if tok in SEED_CORE:
                    rank += 200  # solid core occupation
                elif tok in UNIVERSAL:
                    rank += 80
                if tok in STOPWORDS:
                    rank -= 100
                pool.append((rank, tok))
        # unique keep highest rank
        best: dict[str, int] = {}
        for rank, tok in pool:
            best[tok] = max(best.get(tok, 0), rank)
        ranked = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
        cap = self.max_cands.get(domain, 80)
        out = [tok for tok, _ in ranked[:cap]]
        # ensure universals present
        for u in list(UNIVERSAL) + list(SEED_CORE):
            if u not in out:
                out.append(u)
        if domain not in out and domain in self.vocab:
            out.append(domain)
        if len(out) < 8:
            # sparse organ: fill with high-freq targets for this domain only
            extras = [tok for (d, tok), f in sorted(self.token_freq.items(), key=lambda x: -x[1]) if d == domain]
            for tok in extras:
                if tok not in out and not is_noise_token(tok):
                    out.append(tok)
                if len(out) >= 8:
                    break
        return out

    def forward(
        self,
        text: str,
        domain: str | None = None,
        folds_override: dict | None = None,
    ) -> dict:
        if folds_override is not None:
            if domain:
                self.domain = domain if domain in DOMAIN_FOLDS else self.domain
            self.folds = dict(folds_override)
        elif domain:
            self.set_domain(domain)
        else:
            self.set_domain(infer_domain(text, self.domain))

        toks = tokenize(text) or ["<bos>"]
        folds = dict(self.folds)
        s_ctx = raw_s(
            D_eff=folds["D_eff"],
            delta_psi=folds["delta_psi"],
            observed=folds["observed"],
            recent_hits=self.recent_hits,
        )
        # Modulation from domain scalar — connects context to field amplitude
        mod = 1 + math.tanh(s_ctx)
        mat = [[x * mod for x in self.embed_of(t, self.domain)] for t in toks]
        rot = phase_rotate(mat)
        attn, coh, sim = consensus(rot, rot, rot)
        h = ffn(
            [
                [mat[i][d] + attn[i][d] for d in range(self.dim)]
                for i in range(len(mat))
            ]
        )
        last = h[-1]

        cands = self.candidates_for_domain(self.domain)
        ctx_set = set(toks)
        scores = []
        for tok in cands:
            sc = hybrid_score(last, self.embed_of(tok, self.domain))
            s_tok = raw_s(
                D_eff=folds["D_eff"],
                delta_psi=folds["delta_psi"] * (0.5 + 0.5 * token_unit(tok)),
                observed=folds["observed"],
            )
            # Sign agreement in this D_eff occupation
            sign_bonus = 0.04 if (s_tok * s_ctx) > 0 else -0.03
            # Context affinity: pieces already in the local phrase
            aff = 0.0
            if tok in ctx_set:
                aff += 0.28
            else:
                for ct in ctx_set:
                    if len(ct) >= 4 and len(tok) >= 4 and (ct[:4] == tok[:4] or ct in tok or tok in ct):
                        aff += 0.10
                        break
            # Core / stop priors (same space, different fitness in this organ)
            prior = 0.0
            if tok in SEED_CORE:
                prior += 0.18
            if tok in STOPWORDS:
                prior -= 0.55
            if is_noise_token(tok):
                prior -= 0.40
            # Prefer shorter content for linguistic clarity when scores tie-ish
            if self.domain == "linguistic" and 3 <= len(tok) <= 12 and tok.isalpha():
                prior += 0.03
            total = sc + sign_bonus + aff + prior
            scores.append({
                "token": tok,
                "score": total,
                "S_tok": s_tok,
                "parts": {"hybrid": sc, "sign": sign_bonus, "aff": aff, "prior": prior},
            })
        scores.sort(key=lambda x: -x["score"])
        pred = scores[0]["token"] if scores else "<eos>"

        self.last_trace = {
            "t": datetime.now(timezone.utc).isoformat(),
            "input": text,
            "tokens": toks,
            "domain": self.domain,
            "domain_allocation": {
                "D_eff": folds["D_eff"],
                "delta_psi": folds["delta_psi"],
                "observed": folds["observed"],
                "n_candidates": len(cands),
                "note": "Candidates = tokens allocated to this domain + universal bridges",
            },
            "S_context": s_ctx,
            "modulation": "embed_domain(D_eff spine) * (1 + tanh(S_context))",
            "collapse_threshold": COLLAPSE,
            "mean_coherence": sum(coh) / max(len(coh), 1),
            "top5": scores[:5],
            "prediction": pred,
            "constants": {
                "k": K,
                "c_eff": C_EFF,
                "p_var": P_VAR,
                "poof": POOF,
                "suction": SUCTION,
                "alpha": ALPHA,
                "collapse_threshold": COLLAPSE,
            },
            "ops": [
                "domain_route",
                "embed_on_D_eff_spine",
                "S_context_modulate",
                "phase_rotation",
                "consensus_no_softmax",
                "ffn_phi",
                "score_domain_candidates",
            ],
        }
        return {
            "tokens": toks,
            "hidden_last": last,
            "scores": scores,
            "prediction": pred,
            "domain": self.domain,
            "D_eff": folds["D_eff"],
            "trace": self.last_trace,
        }

    def lr(self, loss: float) -> float:
        eta = (
            abs(SUCTION)
            * abs(POOF)
            * abs(ALPHA)
            * abs(K)
            / (1 + self.recent_hits + abs(loss))
        )
        return max(eta, 1e-8)

    def train_step(self, context: str, target: str, domain: str | None = None) -> dict:
        dom = domain or infer_domain(context, self.domain)
        self.set_domain(dom)
        # Target is a solid member of this organ; context words only if clean
        self.allocate(target, dom, as_target=True)
        for tok in tokenize(context):
            if not is_noise_token(tok):
                self.allocate(tok, dom, as_target=False)
        for u in UNIVERSAL:
            self.allocate(u, dom, as_target=False)

        fwd = self.forward(context, domain=dom)
        last = fwd["hidden_last"]
        et = self.embed_of(target, dom)
        loss = 1.0 - hybrid_score(last, et)
        eta = self.lr(loss)
        # Update domain-specific embedding only
        delta = [eta * (last[i] - et[i]) for i in range(self.dim)]
        new = [et[i] + delta[i] for i in range(self.dim)]
        nrm = math.sqrt(sum(x * x for x in new)) or 1e-12
        self.emb[(dom, target)] = [x / nrm for x in new]
        # Light pull on context tokens in same domain
        for t in tokenize(context):
            key = (dom, t)
            e = self.embed_of(t, dom)
            e2 = [
                e[i] + 0.25 * eta * (self.emb[(dom, target)][i] - e[i])
                for i in range(self.dim)
            ]
            n2 = math.sqrt(sum(x * x for x in e2)) or 1e-12
            self.emb[key] = [x / n2 for x in e2]
        self.recent_hits = min(self.recent_hits + 1.0, 64.0)
        self.step += 1
        log = {
            "step": self.step,
            "context": context,
            "target": target,
            "prediction_before": fwd["prediction"],
            "loss": loss,
            "eta": eta,
            "domain": dom,
            "D_eff": DOMAIN_FOLDS[dom]["D_eff"],
        }
        self.train_log.append(log)
        return log

    def generate_structured(
        self,
        prompt: str,
        n_slots: int | None = None,
        ban_tokens: set[str] | None = None,
        *,
        fluent: bool = True,
        phase: str = "structure",
        phase_index: int = 0,
        domain_override: str | None = None,
        use_bridges: bool = True,
    ) -> dict:
        """
        Multi-token decode by domain slot roles.
        Same numeric scorer; different occupation order per organ (D_eff regime).
        Fills each role by scoring candidates with role-prefer boost + anti-repeat.
        ban_tokens: extra occupation ban (used by paragraph so sentences do not clone).

        fluent=True (default): natural English assembly from the same role map
        (path toward GPT-class surface; content still occupation-scored).
        """
        dom = domain_override or infer_domain(prompt)
        self.set_domain(dom)
        all_slots = load_domain_slots()
        slots = all_slots.get(dom) or all_slots.get("linguistic") or DOMAIN_SLOTS["linguistic"]
        # Default short sentence = up to 8 roles
        n_use = 8 if n_slots is None else max(1, n_slots)
        slots = slots[: min(n_use, len(slots))]
        base = dict(self.folds)
        # Seed prompt into context for affinity
        ctx_tokens = tokenize(prompt)
        filled = []
        steps = []
        used = set()
        ban = set(ban_tokens or [])
        # Prefer keeping prompt anchors if they are SEED_CORE
        for tok in ctx_tokens:
            if tok in SEED_CORE:
                used.add(tok)  # allow re-score but track
        for si, slot in enumerate(slots):
            role = slot["role"]
            prefer = set(slot.get("prefer") or [])
            # Phase along slot index (seed-locked)
            wobble = 0.12 * math.sin(2 * math.pi * PHI * (si + 1) / max(len(slots), 1))
            folds = dict(base)
            folds["D_eff"] = max(3.0, min(25.0, base["D_eff"] + wobble))
            # Context = prompt + filled so far
            ctx = prompt + (" " + " ".join(filled) if filled else "")
            fwd = self.forward(ctx, domain=dom, folds_override=folds)
            scores = [dict(s) for s in fwd["scores"]]
            for s in scores:
                tok = s["token"]
                if tok in filled:
                    s["score"] -= 2.0
                # Paragraph occupation ban always applies (prefer cannot re-use prior sentence seals)
                if tok in ban:
                    s["score"] -= 2.2
                if tok in prefer:
                    # Strong boost only for seed-core or prompt-anchored prefers;
                    # PFLT gold prefers are weaker so "king" does not steal linguistic act/object.
                    if tok in SEED_CORE or tok in ctx_tokens:
                        s["score"] += 0.55
                    else:
                        s["score"] += 0.12
                if tok in ctx_tokens:
                    s["score"] += 0.20
                if tok in STOPWORDS:
                    s["score"] -= 0.6
            scores.sort(key=lambda x: -x["score"])
            # pick best not already filled
            nxt = None
            for s in scores:
                if s["token"] not in filled:
                    nxt = s["token"]
                    break
            if nxt is None:
                nxt = scores[0]["token"] if scores else "field"
            filled.append(nxt)
            steps.append({
                "slot": si + 1,
                "role": role,
                "prefer": sorted(prefer),
                "token": nxt,
                "D_eff": folds["D_eff"],
                "domain": dom,
                "top": scores[:4],
                "score_parts": scores[0].get("parts") if scores else {},
            })
        self.folds = base
        # Classic glue (kept for microscope / backward compatibility)
        glue = {
            "subject": "",
            "link": "in",
            "act": "does",
            "object": "the",
            "state": "as",
            "qual": "with",
            "bridge": "via",
            "close": "toward",
            "seal": "—",
        }
        parts = []
        role_map: dict[str, str] = {}
        for s, tok in zip(steps, filled):
            g = glue.get(s["role"], "")
            if g:
                parts.append(g)
            parts.append(tok)
            role_map[s["role"]] = tok
        sentence_classic = " ".join(parts).replace(" — ", " — ").strip()
        topic = next((t for t in ctx_tokens if t in SEED_CORE), None)
        # Template fluent (fast, closed)
        sentence_template = assemble_fluent(
            role_map,
            phase=phase,
            domain=dom,
            index=phase_index,
            topic=topic,
        )
        # Skeleton + free bridges (path to GPT fluency) — optional sparse tissue
        bridges_doc: dict | None = None
        hybrid_extra: list[str] = []
        sentence_fluent = sentence_template
        if fluent and use_bridges and len(filled) >= 4:
            saved_dom = self.domain
            saved_folds = dict(self.folds)
            try:
                bridges_doc = self.assemble_skeleton_bridges(
                    role_map,
                    prompt,
                    phase=phase,
                    domain=dom,
                    index=phase_index,
                    ban_tokens=ban,
                    topic=topic,
                )
                sentence_fluent = bridges_doc.get("sentence") or sentence_template
                for b in bridges_doc.get("bridges") or []:
                    hybrid_extra.extend(b.get("tokens") or [])
            except Exception:
                bridges_doc = None
                sentence_fluent = sentence_template
            finally:
                self.set_domain(saved_dom)
                self.folds = saved_folds
        sentence = sentence_fluent if fluent else sentence_classic
        if sentence and not sentence[0].isupper():
            sentence = sentence[0].upper() + sentence[1:]
        if sentence and not sentence.endswith("."):
            sentence += "."
        mode = "structured_slots_v2"
        if fluent and use_bridges and bridges_doc:
            mode = "structured_slots_v4_bridges"
        elif fluent:
            mode = "structured_slots_v3_fluent"
        return {
            "prompt": prompt,
            "mode": mode,
            "domain": dom,
            "D_eff": base["D_eff"],
            "generated": " ".join(filled),
            "sentence": sentence,
            "sentence_classic": sentence_classic,
            "sentence_template": sentence_template,
            "sentence_fluent": sentence_fluent,
            "tokens": filled,
            "role_map": role_map,
            "hybrid_extra": hybrid_extra[:24],
            "bridges": (bridges_doc or {}).get("bridges"),
            "n_roles": len(filled),
            "steps": steps,
            "phase": phase,
            "formula": (
                "for role in slots[1..8]: argmax(score + role_prefer - filled_ban); "
                "fluent = template | skeleton + sparse free_bridge tissue"
            ),
        }

    def generate_paragraph(
        self,
        prompt: str,
        n_sentences: int = 6,
        n_slots: int = 8,
        *,
        fluent: bool = True,
        on_step=None,
    ) -> dict:
        """
        Paragraph = ordered sequence of domain-slot sentences + seed connector lines.

        Default 6-sentence arc:
          emergence → structure → interaction → consequence(connector)
          → measure → seal

        fluent=True (default): natural English assembly + varied connectors
        (path toward GPT fluency; occupation spine unchanged).

        on_step: optional callback(step_dict) after each sentence/connector
        for streaming deep arcs in chat.
        """
        root_dom = infer_domain(prompt)
        self.set_domain(root_dom)
        base = dict(DOMAIN_FOLDS[root_dom])
        ctx_toks = tokenize(prompt)
        anchors = [t for t in ctx_toks if t in SEED_CORE]
        if len(anchors) < 3:
            # domain-tinted anchors
            dom_seed = {
                "linguistic": ["fsot", "fluid", "language", "meaning", "truth", "seed"],
                "quantum": ["quantum", "collapse", "trinary", "measure", "field", "seed"],
                "medical": ["medical", "diagnose", "signal", "measure", "truth", "field"],
                "neural": ["neural", "consciousness", "observe", "mind", "field", "seed"],
                "mythological": ["earth", "sky", "create", "form", "truth", "life"],
                "cosmological": ["spacetime", "scalar", "phase", "seed", "phi", "field"],
                "chemical": ["structure", "energy", "code", "transfer", "seed", "field"],
                "genomic": ["codon", "transfer", "start", "code", "life", "action"],
                "biological": ["life", "biology", "structure", "form", "code", "field"],
                "consciousness": ["consciousness", "observe", "mind", "field", "truth", "seed"],
            }
            anchors = list(dict.fromkeys(anchors + dom_seed.get(root_dom, list(SEED_CORE)[:6])))

        # Full rhetorical arc; default take 6
        full_arc = [
            ("emergence", "sentence"),
            ("structure", "sentence"),
            ("interaction", "sentence"),
            ("consequence", "connector"),  # Therefore …
            ("measure", "sentence"),
            ("coherence", "connector"),  # Thus …
            ("verification", "connector"),  # Hence …
            ("seal", "sentence"),
        ]
        # Prefer a clean 6-step publication arc
        arc_6 = [
            ("emergence", "sentence"),
            ("structure", "sentence"),
            ("interaction", "sentence"),
            ("consequence", "connector"),
            ("measure", "sentence"),
            ("seal", "sentence"),
        ]
        if n_sentences <= 6:
            arc = arc_6[: max(1, n_sentences)]
            # if user asks 6, use full arc_6; if 5 drop seal; etc.
            if n_sentences == 6:
                arc = arc_6
            elif n_sentences == 5:
                arc = [
                    ("emergence", "sentence"),
                    ("structure", "sentence"),
                    ("consequence", "connector"),
                    ("measure", "sentence"),
                    ("seal", "sentence"),
                ]
        else:
            arc = full_arc[: max(1, min(n_sentences, 8))]

        neighbors = {
            "linguistic": "consciousness",
            "quantum": "cosmological",
            "medical": "neural",
            "neural": "consciousness",
            "mythological": "linguistic",
            "cosmological": "quantum",
            "chemical": "biological",
            "genomic": "biological",
            "biological": "genomic",
            "consciousness": "neural",
        }

        def pick_fill(pool: list[str], ban: set[str], i: int) -> str:
            opts = [x for x in pool if x not in ban]
            if not opts:
                opts = pool or ["field"]
            return opts[int(i * PHI * 3) % len(opts)]

        sentences: list[str] = []
        steps: list[dict] = []
        used_seals: list[str] = []
        for i, (phase, kind) in enumerate(arc):
            focus = anchors[int(i * PHI) % len(anchors)]
            ban = set(used_seals)
            ban -= set(anchors[:3])

            if kind == "connector":
                a = pick_fill(anchors, ban, i)
                b = pick_fill(anchors, ban | {a}, i + 1)
                c = pick_fill(
                    anchors + ["truth", "effect", "consensus", "seed", "field"],
                    ban | {a, b},
                    i + 2,
                )
                if fluent:
                    text = assemble_fluent_connector(phase, a, b, c, index=i)
                else:
                    templates = {
                        "consequence": f"Therefore {a} joins {b} toward {c}",
                        "coherence": f"Thus {a} and {b} hold consensus in the field of {c}",
                        "verification": f"Hence {a} verifies {b} against seed {c}",
                        "transition": f"As above, so below: {a} maps into {b} via {c}",
                    }
                    raw = templates.get(phase, templates["consequence"])
                    text = raw[0].upper() + raw[1:] + "."
                sentences.append(text)
                step_c = {
                    "index": i + 1,
                    "phase": phase,
                    "kind": "connector",
                    "focus": focus,
                    "domain": root_dom,
                    "D_eff": base["D_eff"],
                    "sentence": text,
                    "fills": {"a": a, "b": b, "c": c},
                    "template": phase,
                    "tokens": [a, b, c],
                    "roles": [],
                }
                steps.append(step_c)
                if on_step is not None:
                    try:
                        on_step(step_c)
                    except Exception:
                        pass
                used_seals.extend([a, b, c])
                continue

            # sentence occupation
            bridge_dom = root_dom
            if phase in ("interaction", "measure") and i > 0:
                bridge_dom = neighbors.get(root_dom, root_dom)
            phase_cue = {
                "emergence": f"{prompt} {focus} emerge field",
                "structure": f"{prompt} {focus} structure form domain",
                "interaction": f"{prompt} {focus} interact communicate",
                "measure": f"{prompt} {focus} measure observe",
                "seal": f"{prompt} {focus} seed parameter seal truth",
                "coherence": f"{prompt} {focus} consensus field",
                "verification": f"{prompt} {focus} verify seed truth",
            }.get(phase, f"{prompt} {focus} field structure")
            use_dom = bridge_dom if phase in ("interaction", "measure") else root_dom
            self.set_domain(use_dom)
            folds = dict(DOMAIN_FOLDS[self.domain])
            folds["D_eff"] = max(
                3.0,
                min(
                    25.0,
                    folds["D_eff"]
                    + 0.2 * math.sin(2 * math.pi * PHI * (i + 1) / max(len(arc), 1)),
                ),
            )
            self.folds = folds
            sent = self.generate_structured(
                phase_cue,
                n_slots=n_slots,
                ban_tokens=ban,
                fluent=fluent,
                phase=phase if phase in (
                    "emergence", "structure", "interaction", "measure", "seal",
                    "coherence", "verification",
                ) else "structure",
                phase_index=i,
                domain_override=use_dom,
            )
            text = sent.get("sentence") or sent.get("generated") or ""
            if text:
                text = text[0].upper() + text[1:]
                if not text.endswith("."):
                    text += "."
            sentences.append(text)
            step_s = {
                "index": i + 1,
                "phase": phase,
                "kind": "sentence",
                "focus": focus,
                "domain": sent.get("domain"),
                "D_eff": sent.get("D_eff"),
                "sentence": text,
                "sentence_classic": sent.get("sentence_classic"),
                "tokens": sent.get("tokens"),
                "role_map": sent.get("role_map"),
                "hybrid_extra": sent.get("hybrid_extra"),
                "roles": [
                    {"role": s["role"], "token": s["token"]}
                    for s in sent.get("steps") or []
                ],
            }
            steps.append(step_s)
            if on_step is not None:
                try:
                    on_step(step_s)
                except Exception:
                    pass
            used_seals.extend(sent.get("tokens") or [])

        self.set_domain(root_dom)
        # Discourse packing: join with light space (fluent sentences already punctuated)
        paragraph = " ".join(sentences)
        return {
            "prompt": prompt,
            "mode": "paragraph_v3_fluent" if fluent else "paragraph_v2",
            "domain": root_dom,
            "D_eff": base["D_eff"],
            "n_sentences": len(sentences),
            "paragraph": paragraph,
            "sentences": sentences,
            "steps": steps,
            "arc": [p for p, _ in arc],
            "fluent": fluent,
            "formula": (
                "paragraph_v3 = concat steps; "
                "step = fluent_template(role_map) | connector(Φ English + seed fills); "
                "hybrid micro-fill optional; default arc 6; deep arc 8"
            ),
            "ontology_note": (
                "Surface fluency is closed Φ-templates over occupation skeletons. "
                "Direction still seeds + D_eff; not free-parameter prose models."
            ),
        }

    def generate(
        self,
        prompt: str,
        n: int = 12,
        *,
        ban_tokens: set[str] | None = None,
        domain_override: str | None = None,
        prefer_content: bool = True,
    ) -> dict:
        """
        Autoregressive generation with local non-repeat dynamics.
        Same organ can reuse structure, but not stutter the same cell forever
        (phase diversity via recent ban + soft D_eff wobble).
        """
        if domain_override:
            self.set_domain(domain_override)
        else:
            self.set_domain(infer_domain(prompt))
        ctx = prompt
        out = []
        steps = []
        banned: list[str] = list(ban_tokens or [])  # recent occupation — cannot re-fire immediately
        hard_ban = set(ban_tokens or [])
        base_folds = dict(self.folds)
        for i in range(n):
            # Soft phase diversity: tiny seed-locked D_eff wobble per step (not free param)
            wobble = 0.15 * math.sin(2 * math.pi * PHI * (i + 1) / max(n, 1))
            wobble_folds = dict(base_folds)
            wobble_folds["D_eff"] = max(3.0, min(25.0, base_folds["D_eff"] + wobble))
            wobble_folds["delta_psi"] = max(
                0.05, min(2.5, base_folds["delta_psi"] + 0.05 * math.cos(i * PHI))
            )
            fwd = self.forward(ctx, domain=self.domain, folds_override=wobble_folds)
            # Re-score with bans: local interaction cannot loop same token
            scores = [dict(s) for s in fwd["scores"]]  # copy
            # Anti-cycle penalties (local occupation cannot loop forever)
            bigrams = set(zip(out, out[1:])) if len(out) >= 2 else set()
            trigrams = set(zip(out, out[1:], out[2:])) if len(out) >= 3 else set()
            for s in scores:
                tok = s["token"]
                if tok in hard_ban:
                    s["score"] -= 2.4
                if tok in banned[-8:]:
                    s["score"] -= 1.8
                if out and tok == out[-1]:
                    s["score"] -= 2.5
                if len(out) >= 2 and tok == out[-2]:
                    s["score"] -= 1.0
                # bigram repeat: (... a b) then b again starting a b
                if out and (out[-1], tok) in bigrams:
                    s["score"] -= 2.2
                if len(out) >= 2 and (out[-2], out[-1], tok) in trigrams:
                    s["score"] -= 2.8
                # novelty: prefer unseen in this generation
                if tok in out:
                    s["score"] -= 0.35 * out.count(tok)
                if prefer_content:
                    if is_noise_token(tok) and tok not in UNIVERSAL:
                        s["score"] -= 1.5
                    if tok in SEED_CORE or tok in UNIVERSAL:
                        s["score"] += 0.12
                    if tok in STOPWORDS:
                        s["score"] -= 0.25  # allow light function words in free bridges
            scores.sort(key=lambda x: -x["score"])
            nxt = scores[0]["token"] if scores else "<eos>"
            if nxt in ("<eos>", "<pad>"):
                break
            # force novelty if top is exhausted loop
            if out.count(nxt) >= 2:
                for s in scores[1:]:
                    if out.count(s["token"]) == 0 and s["token"] not in banned[-3:]:
                        nxt = s["token"]
                        break
            if out and nxt == out[-1]:
                for s in scores[1:]:
                    if s["token"] != nxt:
                        nxt = s["token"]
                        break
            out.append(nxt)
            banned.append(nxt)
            if len(banned) > 12:
                banned = banned[-12:]
            steps.append(
                {
                    "step": i + 1,
                    "next": nxt,
                    "domain": fwd["domain"],
                    "D_eff": self.folds["D_eff"],
                    "banned": list(banned[-5:]),
                    "top": scores[:3],
                }
            )
            ctx = ctx + " " + nxt
        # restore folds
        self.folds = base_folds
        return {
            "prompt": prompt,
            "generated": " ".join(out),
            "tokens": out,
            "domain": self.domain,
            "steps": steps,
        }

    def generate_bridge(
        self,
        left: str,
        right: str,
        prompt: str = "",
        *,
        n_min: int = 5,
        n_max: int = 12,
        ban_tokens: set[str] | None = None,
        domain: str | None = None,
        index: int = 0,
    ) -> dict:
        """
        Free bridge between skeleton anchors (path to GPT fluency).

        Closed phrase (Φ) + 5–12 scored free tokens with strong diet/ban.
        Content anchors left/right stay fixed; bridge is the readable tissue.
        """
        dom = domain or self.domain
        self.set_domain(dom)
        n = n_min + int((index + 1) * PHI) % max(1, n_max - n_min + 1)
        n = max(n_min, min(n_max, n))
        ban = set(ban_tokens or [])
        ban |= {left, right}
        phrase = bridge_phrase(index, salt=len(left) + len(right))
        ctx = f"{prompt} {left} {phrase}".strip()
        fre = self.generate(
            ctx,
            n=n,
            ban_tokens=ban,
            domain_override=dom,
            prefer_content=True,
        )
        # keep only clean open-class-ish tokens; drop pure noise / pure repeats of left/right
        toks: list[str] = []
        for t in fre.get("tokens") or []:
            if t in ban or t in (left, right):
                continue
            if is_noise_token(t) and t not in UNIVERSAL and t not in SEED_CORE:
                continue
            if t in toks:
                continue
            toks.append(t)
            if len(toks) >= n:
                break
        # guarantee at least a short content trail
        if len(toks) < 2:
            for filler in ("field", "structure", "meaning", "seed", "truth", "measure"):
                if filler not in ban and filler not in toks:
                    toks.append(filler)
                if len(toks) >= 3:
                    break
        mid = " ".join(toks[:n])
        text = f"{phrase} {mid}".strip()
        text = re.sub(r"\s+", " ", text)
        return {
            "left": left,
            "right": right,
            "phrase": phrase,
            "tokens": toks[:n],
            "text": text,
            "n": len(toks[:n]),
            "domain": dom,
            "mode": "bridge_v1",
            "formula": "bridge = Φ-phrase + free_gen(5..12) with ban/diet; anchors fixed",
        }

    def assemble_skeleton_bridges(
        self,
        role_map: dict[str, str],
        prompt: str = "",
        *,
        phase: str = "structure",
        domain: str = "linguistic",
        index: int = 0,
        ban_tokens: set[str] | None = None,
        topic: str | None = None,
    ) -> dict:
        """
        Full fluent sentence: English template spine + sparse free bridges.

        GPT-path rule: free-gen is *tissue*, not a token dump.
        Each bridge contributes Φ-phrase + 1–3 clean content tokens only.
        """
        sub = role_map.get("subject") or "field"
        act = role_map.get("act") or "observe"
        obj = role_map.get("object") or role_map.get("state") or "structure"
        close = role_map.get("close") or "truth"
        seal = role_map.get("seal") or "seed"
        link = role_map.get("link") or "field"
        qual = role_map.get("qual") or "structure"
        bridge_role = role_map.get("bridge") or domain
        vs = verb_s(act)
        ban = set(ban_tokens or []) | set(role_map.values())
        prompt_toks = set(tokenize(prompt))

        # Richer free tissue after full retrain: up to 3 content tokens per bridge,
        # still dieted (seed/universal/prompt + domain-allocated alpha words).
        domain_alloc = set()
        for tok, doms in getattr(self, "token_domains", {}).items():
            if domain in doms and tok.isalpha() and 3 <= len(tok) <= 14:
                domain_alloc.add(tok)

        def sparse_bridge(left: str, right: str, i: int) -> dict:
            """Phrase + 1–3 high-quality free tokens (richer post-retrain tissue)."""
            b = self.generate_bridge(
                left,
                right,
                prompt,
                n_min=6,
                n_max=12,
                ban_tokens=ban,
                domain=domain,
                index=i,
            )
            clean: list[str] = []
            holdout = {"pi", "phi", "euler", "catalan", "gamma"}
            for t in b.get("tokens") or []:
                if t in ban or t in (left, right, sub, act, obj, close, seal, link):
                    continue
                if t in holdout:
                    continue
                if is_noise_token(t) and t not in UNIVERSAL:
                    continue
                ok = (
                    t in SEED_CORE
                    or t in UNIVERSAL
                    or t in prompt_toks
                    or t in domain_alloc
                )
                if ok and t not in clean:
                    clean.append(t)
                if len(clean) >= 3:
                    break
            # fallback one domain-ish seed if empty
            if not clean:
                for fb in ("field", "structure", "meaning", "seed", "truth", "measure"):
                    if fb not in ban and fb not in (left, right, sub, act, obj):
                        clean.append(fb)
                        break
            ban.update(clean)
            phrase = b.get("phrase") or bridge_phrase(i)
            # surface: phrase + up to 2 free tokens not already in the phrase
            extras = [t for t in clean if t not in phrase.lower()][:2]
            tissue = " ".join(extras)
            return {
                "left": left,
                "right": right,
                "phrase": phrase,
                "tokens": clean,
                "text": f"{phrase} {tissue}".strip() if tissue else phrase,
                "n": len(clean),
            }

        b1 = sparse_bridge(sub, act, index)
        b2 = sparse_bridge(act, obj, index + 1)
        b3 = sparse_bridge(obj, close, index + 2)

        openers = {
            "emergence": f"At first {sub}",
            "structure": f"In the {link} {sub}",
            "interaction": f"As it meets {bridge_role} {sub}",
            "measure": f"Under measure {sub}",
            "seal": f"Finally {sub}",
            "coherence": f"Holding together {sub}",
            "verification": f"Checked against seed {sub}",
        }
        head = openers.get(phase, f"In the {link} {sub}")
        if topic and topic not in head.lower() and index % 2 == 0:
            head = f"On {topic}, " + head[0].lower() + head[1:]

        # Template spine with sparse bridge tissue (not a free-token list)
        # Pattern: Head, {phrase1} {tok}, {verb}s the {obj} with {qual}
        #          {phrase2} {tok}, toward {close} — {seal}.
        mid1 = b1["text"]
        mid2 = b2["text"] if b2["phrase"] != b1["phrase"] else (
            f"through the medium of {b2['tokens'][0]}" if b2["tokens"] else "through the medium of structure"
        )
        # Optional third bridge only as soft tail if distinct
        soft = ""
        if b3["tokens"] and b3["tokens"][0] not in mid1 and b3["tokens"][0] not in mid2:
            soft = f" and {b3['phrase']} {b3['tokens'][0]}"

        body = (
            f"{head}, {mid1}, {vs} the {obj} with {qual}, "
            f"{mid2}{soft}, toward {close} — {seal}"
        )

        text = re.sub(r"\s+", " ", body).strip()
        text = re.sub(r"\s+([,.—])", r"\1", text)
        text = re.sub(r"\b(\w{4,})\s+\1\b", r"\1", text, flags=re.I)
        text = re.sub(r",\s*,", ",", text)
        text = re.sub(r"\s+—\s+", " — ", text)
        if not text.endswith("."):
            text += "."
        if text[0].islower():
            text = text[0].upper() + text[1:]
        return {
            "sentence": text,
            "bridges": [b1, b2, b3],
            "anchors": {
                "subject": sub,
                "act": act,
                "object": obj,
                "close": close,
                "seal": seal,
            },
            "mode": "skeleton_bridges_v4_rich",
            "formula": (
                "English template + 3× (Φ-phrase + ≤3 seed/universal/prompt/domain tokens); "
                "free-gen is tissue not dump; anchors fixed; richer post full retrain"
            ),
        }

    def verify_authority(self) -> dict:
        if not AUTH.exists():
            return {"ok": False, "reason": "missing authority json"}
        auth = json.loads(AUTH.read_text(encoding="utf-8"))
        kc = auth["kernel_constants"]
        pairs = [
            ("k", K, kc["k_fsot"]),
            ("c_eff", C_EFF, kc["c_eff"]),
            ("p_var", P_VAR, kc["p_var"]),
            ("poof", POOF, kc["poof"]),
            ("suction", SUCTION, kc["suction"]),
            ("alpha", ALPHA, kc["alpha_fsot"]),
            ("c_factor", C_FACTOR, kc["c_factor"]),
        ]
        rows = []
        ok = True
        for name, got, ref in pairs:
            err = abs(got - ref) / max(abs(ref), 1e-15)
            rows.append({"symbol": name, "got": got, "ref": ref, "rel_err": err})
            if err > 1e-6:
                ok = False
        coll_ref = kc["c_eff"] * kc["p_var"]
        err_c = abs(COLLAPSE - coll_ref) / max(abs(coll_ref), 1e-15)
        rows.append(
            {
                "symbol": "collapse_threshold",
                "got": COLLAPSE,
                "ref": coll_ref,
                "rel_err": err_c,
            }
        )
        if err_c > 1e-6:
            ok = False
        return {"ok": ok, "rows": rows, "boot": auth["boot"]["boot_scalar_canonical"]}

    def save(self) -> None:
        MEM.mkdir(parents=True, exist_ok=True)
        TRACES.mkdir(parents=True, exist_ok=True)
        # Serialize domain allocations + a sample of embeds
        alloc = {t: sorted(list(ds)) for t, ds in self.token_domains.items()}
        # Store embeddings as "domain::token" keys for JSON
        emb_out = {f"{d}::{t}": v for (d, t), v in self.emb.items()}
        doc = {
            "id": "FSOT-LLM-DomainAlloc-1",
            "version": "1.1.0",
            "saved": datetime.now(timezone.utc).isoformat(),
            "dim": self.dim,
            "vocab": self.vocab,
            "domain": self.domain,
            "folds": self.folds,
            "domain_folds_table": DOMAIN_FOLDS,
            "token_domain_allocation": alloc,
            "recent_hits": self.recent_hits,
            "step": self.step,
            "embeddings": emb_out,
            "train_log_tail": self.train_log[-50:],
            "constants": self.last_trace.get("constants")
            or {"k": K, "c_eff": C_EFF, "collapse_threshold": COLLAPSE},
            "note": "Domain allocation + D_eff spine embeds. Pieces connect per domain.",
        }
        MODEL_OUT.write_text(json.dumps(doc), encoding="utf-8")
        if self.last_trace:
            TRACE_OUT.write_text(json.dumps(self.last_trace, indent=2), encoding="utf-8")


def main() -> int:
    TRACES.mkdir(parents=True, exist_ok=True)
    MEM.mkdir(parents=True, exist_ok=True)

    # Phase: refresh PFLT-derived slot prefers
    try:
        from build_domain_prefer_lists import main as _build_prefers
        _build_prefers()
    except Exception as e:
        print("prefer list build skipped:", e)

    print("=== FSOT LLM BOOT (domain allocation + D_eff) ===")
    vocab = None
    if VOCAB.exists():
        vocab = json.loads(VOCAB.read_text(encoding="utf-8"))["tokens"]
        print(f"vocab loaded: {len(vocab)} tokens")
    model = FSOTLLM(dim=32, vocab=vocab)

    print("\n=== AUTHORITY VERIFY ===")
    v = model.verify_authority()
    print("ok:", v.get("ok"))
    for r in v.get("rows", []):
        print(f"  {r['symbol']}: rel_err={r['rel_err']:.3e}")

    if not CUR.exists():
        print("Missing curriculum", file=sys.stderr)
        return 1
    pairs = json.loads(CUR.read_text(encoding="utf-8"))["pairs"]
    # Prefer meaning-bearing sources; classical dump held out of primary train
    pairs = [
        p
        for p in pairs
        if not str(p.get("source", "")).startswith(("classical", "hieroglyph"))
    ]
    print(f"\n=== CURRICULUM: {len(pairs)} pairs (quality-filtered) ===")

    # Pre-allocate: targets solidly occupy domain; context only if clean
    for row in pairs:
        dom = row.get("domain") or "linguistic"
        model.allocate(row["target"], dom, as_target=True)
        for tok in tokenize(row["context"]):
            if not is_noise_token(tok):
                model.allocate(tok, dom, as_target=False)

    def by_source(prefix: str):
        return [p for p in pairs if str(p.get("source", "")).startswith(prefix)]

    seed_p = by_source("seed")
    hist_p = by_source("historical")
    dom_p = by_source("domain")
    ros_p = by_source("rosetta")
    flu_p = by_source("fluency")
    safe_p = by_source("global_safe")
    sci_p = [
        p
        for p in pairs
        if p.get("domain")
        in (
            "medical",
            "genomic",
            "quantum",
            "neural",
            "chemical",
            "biological",
            "consciousness",
            "cosmological",
        )
    ]
    med_p = [p for p in pairs if p.get("domain") == "medical"]
    print(
        f"  bags: seed={len(seed_p)} hist={len(hist_p)} dom={len(dom_p)} "
        f"sci={len(sci_p)} ros={len(ros_p)} flu={len(flu_p)} med={len(med_p)} safe={len(safe_p)}"
    )

    def make_epoch(ep: int, n: int = 1800):
        rng = random.Random(42 + ep)
        mix = []
        # Fluency discourse elevated — path to GPT-class surface geometry
        bags = [
            (seed_p, 0.18),
            (hist_p, 0.22),
            (dom_p, 0.14),
            (sci_p, 0.16),
            (ros_p, 0.08),
            (flu_p, 0.14),
            (med_p, 0.05),
            (safe_p, 0.03),
        ]
        for bag, frac in bags:
            if not bag:
                continue
            k = max(1, int(n * frac))
            mix.extend(rng.choices(bag, k=k) if len(bag) < k else rng.sample(bag, k))
        rng.shuffle(mix)
        return mix[:n]

    epochs = 3
    print(f"\n=== TRAIN epochs={epochs} (domain-stratified + fluency) ===")
    losses = []
    for ep in range(epochs):
        batch = make_epoch(ep)
        for row in batch:
            log = model.train_step(row["context"], row["target"], row.get("domain"))
            losses.append(log["loss"])
            if log["step"] % 200 == 0:
                print(
                    f"    step {log['step']} dom={log['domain']} D_eff={log['D_eff']} "
                    f"loss={log['loss']:.4f} pred={log['prediction_before']} tgt={log['target']}"
                )
        tail = losses[-50:]
        print(f"  epoch {ep+1}: steps={len(batch)} mean_loss_tail={sum(tail)/len(tail):.4f}")

    print("\n=== FINE-TUNE seed + fluency + science + medical ===")
    seed_all = [p for p in pairs if str(p.get("source", "")).startswith("seed")]
    flu_all = flu_p if flu_p else []
    ft = (
        (seed_all * 80)
        + (flu_all * 40)
        + sci_p
        + med_p * 8
        + dom_p[:150]
        + [p for p in hist_p if p.get("target") in SEED_CORE] * 5
    )
    random.Random(7).shuffle(ft)
    ft = ft[:1600]
    for row in ft:
        log = model.train_step(row["context"], row["target"], row.get("domain"))
        losses.append(log["loss"])
    print(f"  fine-tune steps={len(ft)} mean_loss_tail={sum(losses[-40:])/40:.4f}")

    print("\n=== FORWARD (domain-routed) ===")
    for prompt in [
        "fluid spacetime language translate",
        "quantum measure collapse",
        "medical signal diagnose",
        "sky earth time create",
        "start transfer energy structure",
        "proto fluid communicate",
        "neural consciousness observe",
    ]:
        fwd = model.forward(prompt)
        print(
            f"  [{prompt!r}]\n"
            f"    domain={fwd['domain']} D_eff={fwd['D_eff']} → {fwd['prediction']}\n"
            f"    top3={fwd['scores'][:3]}"
        )

    print("\n=== GENERATE (free + anti-cycle) ===")
    gens = []
    for prompt in [
        "fsot scalar seed domain",
        "proto fluid communicate",
        "neural consciousness observe",
        "medical signal measure",
    ]:
        g = model.generate(prompt, n=8)
        gens.append(g)
        print(f"  free {prompt!r} [{g['domain']}] => {g['generated']}")

    print("\n=== GENERATE STRUCTURED (domain slots) ===")
    structured = []
    for prompt in [
        "fsot scalar seed domain",
        "proto fluid communicate",
        "neural consciousness observe",
        "medical signal measure",
        "quantum measure collapse",
        "sky earth time create",
    ]:
        g = model.generate_structured(prompt)
        structured.append(g)
        print(f"  slot {prompt!r} [{g['domain']} D_eff={g['D_eff']}] => {g['generated']}")
        if g.get("sentence"):
            print(f"       sentence: {g['sentence']}")
        print(f"       roles: " + " | ".join(f"{s['role']}={s['token']}" for s in g["steps"]))

    # Microscope export for Mathematica: score boards + structured steps
    micro_dir = DATA / "microscope"
    micro_dir.mkdir(parents=True, exist_ok=True)
    boards = []
    for prompt, cand_a, cand_b, dom in [
        ("proto fluid communicate", "communicate", "finance", "linguistic"),
        ("medical signal diagnose", "diagnose", "finance", "medical"),
        ("quantum measure collapse", "measure", "king", "quantum"),
        ("fluid spacetime language translate", "translate", "gaul", "linguistic"),
        ("sky earth time create", "earth", "finance", "mythological"),
    ]:
        model.set_domain(dom)
        fwd = model.forward(prompt, domain=dom)
        # find parts for candidates
        by_tok = {s["token"]: s for s in fwd["scores"]}
        def row(tok):
            s = by_tok.get(tok) or {"token": tok, "score": None, "parts": {}, "S_tok": None}
            return {
                "token": tok,
                "score": s.get("score"),
                "S_tok": s.get("S_tok"),
                "parts": s.get("parts") or {},
                "in_candidates": tok in by_tok,
            }
        boards.append({
            "prompt": prompt,
            "domain": dom,
            "D_eff": DOMAIN_FOLDS[dom]["D_eff"],
            "prediction": fwd["prediction"],
            "winner_parts": (by_tok.get(fwd["prediction"]) or {}).get("parts"),
            "compare": [row(cand_a), row(cand_b)],
            "top5": fwd["scores"][:5],
            "S_context": fwd["trace"].get("S_context"),
        })
    micro = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Import in Mathematica for formula microscope plots",
        "score_boards": boards,
        "structured_generations": structured,
        "free_generations": gens,
        "formulas": {
            "total": "0.55*cos + 0.45*trit_sim + sign + affinity + prior",
            "eta": "|suction|*|poof|*|alpha|*|K|/(1+hits+|loss|)",
            "collapse": "C_eff * P_var",
            "slot_decode": "argmax_tok score + role_prefer_boost - filled_ban",
        },
    }
    micro_path = micro_dir / "score_boards.json"
    micro_path.write_text(json.dumps(micro, indent=2), encoding="utf-8")
    print(f"\n=== MICROSCOPE EXPORT ===\n  {micro_path}")

    print("\n=== EXPLICIT DOMAIN SET ===")
    cand_sizes = {}
    for d in ["linguistic", "quantum", "medical", "mythological", "genomic", "cosmological"]:
        model.set_domain(d)
        cands = model.candidates_for_domain(d)
        cand_sizes[d] = len(cands)
        r = model.forward("structure energy field", domain=d)
        print(f"  {d} (D_eff={r['D_eff']}) → {r['prediction']}  cands={len(cands)}")
    print("\n=== ROUTING CHECK ===")
    for prompt in [
        "fluid spacetime language translate",
        "spacetime galaxy hubble",
        "fluid communicate meaning",
    ]:
        d = infer_domain(prompt)
        print(f"  {prompt!r} → {d} (D_eff={DOMAIN_FOLDS[d]['D_eff']})")

    model.save()
    report = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "authority_ok": v.get("ok"),
        "architecture": "domain_allocation_D_eff_spine",
        "n_pairs": len(pairs),
        "train_steps": model.step,
        "mean_loss_last_100": sum(losses[-100:]) / max(len(losses[-100:]), 1),
        "vocab_n": len(model.vocab),
        "n_domain_embed_keys": len(model.emb),
        "allocation_sizes": {
            d: sum(1 for t, ds in model.token_domains.items() if d in ds)
            for d in DOMAIN_FOLDS
        },
        "candidate_diet_sizes": cand_sizes,
        "generations": gens,
        "structured_generations": structured,
        "microscope_path": str(DATA / "microscope" / "score_boards.json"),
        "model_path": str(MODEL_OUT),
        "trace_path": str(TRACE_OUT),
    }
    RUN_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n=== SAVED ===")
    print(MODEL_OUT)
    print(TRACE_OUT)
    print(RUN_REPORT)
    print("BOOT COMPLETE authority_ok=", v.get("ok"), "steps=", model.step)
    return 0 if v.get("ok") else 1


if __name__ == "__main__":
    random.seed(7)
    raise SystemExit(main())
