#!/usr/bin/env python3
"""Build 6–8 role domain slot prefer lists from curriculum + live PFLT lexica."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
CUR = DATA / "fsot_llm_curriculum.json"
OUT = DATA / "domain_slot_prefers.json"
PFLT = Path(r"C:\Users\damia\Desktop\pflt\data")

# Map PFLT scientific domain names → FSOT LLM organs
PFLT_TO_FSOT = {
    "linguistics": "linguistic",
    "linguistics_formal": "linguistic",
    "psychology": "consciousness",
    "neuroscience": "neural",
    "quantum_mechanics": "quantum",
    "quantum": "quantum",
    "particle_physics": "quantum",
    "nuclear_physics": "quantum",
    "cosmology": "cosmological",
    "astronomy": "cosmological",
    "astrophysics": "cosmological",
    "chemistry": "chemical",
    "physical_chemistry": "chemical",
    "biology": "biological",
    "biochemistry": "biological",
    "genetics": "genomic",
    "medicine": "medical",
    "medical": "medical",
    "consciousness": "consciousness",
}

ROLE_ORDER = [
    "subject", "link", "act", "object", "state", "qual", "bridge", "close", "seal",
]

SEED_CORE = {
    "fsot", "fluid", "spacetime", "seed", "scalar", "domain", "structure",
    "energy", "field", "phase", "flow", "translate", "communicate", "language",
    "meaning", "observe", "collapse", "trinary", "consensus", "proof", "truth",
    "measure", "verify", "parameter", "theory", "omni", "universal", "proto",
    "diagnose", "medical", "mind", "consciousness", "form", "create", "action",
    "start", "transfer", "code", "therefore", "cause", "effect",
    "pi", "phi", "euler", "catalan", "quantum", "neural", "chemical",
    "biological", "genomic", "signal", "life", "structure",
}

QUALITY = {
    "water", "river", "king", "sky", "earth", "law", "god", "son", "female",
    "mount", "man", "house", "land", "fire", "day", "time", "life", "word",
    "name", "hand", "eye", "heart", "blood", "stone", "tree", "bird", "fish",
    "mother", "father", "city", "road", "gold", "silver", "wind", "rain",
    "sun", "moon", "star", "sea", "food", "bread", "wine", "horse", "dog",
    "field", "form", "judgment", "tablet",
}

NOISE = re.compile(r"^(cve|the|a|an|if|or|and|of|to|in|is)$")
BAD_SUB = ("clinicaltrials", "mediated", "media", "chaos", "arxiv", "founding", "_aspect", "_flow")


def clean(tok: str) -> bool:
    t = (tok or "").strip().lower().replace(" ", "_")
    if not t or len(t) < 2 or len(t) > 20:
        return False
    if NOISE.match(t):
        return False
    if any(b in t for b in BAD_SUB):
        return False
    if t.startswith(("a_", "an_")):
        return False
    if not re.match(r"^[a-z][a-z0-9_]*$", t):
        return False
    return True


def tokenize_meaning(s: str) -> list[str]:
    s = re.sub(r"[^a-z0-9_\s]", " ", (s or "").lower())
    return [w for w in re.split(r"[\s_]+", s) if clean(w)]


# 8-role anchors per domain
def anchors(domain: str) -> dict[str, list[str]]:
    table = {
        "linguistic": {
            "subject": ["fsot", "fluid", "proto", "language", "universal"],
            "link": ["field", "domain", "structure", "phase"],
            "act": ["translate", "communicate", "verify", "observe"],
            "object": ["meaning", "language", "seed", "scalar", "formula"],
            "qual": ["structure", "consensus", "parameter", "theory"],
            "bridge": ["spacetime", "fluid", "omni", "theory"],
            "close": ["truth", "proof", "verify", "theory"],
            "seal": ["fsot", "seed", "consensus", "parameter"],
        },
        "quantum": {
            "subject": ["quantum", "particle", "nuclear", "field"],
            "link": ["phase", "structure", "field"],
            "act": ["collapse", "measure", "observe"],
            "state": ["trinary", "superposed", "structure"],
            "object": ["measure", "field", "seed"],
            "qual": ["consensus", "coherence", "phase"],
            "close": ["truth", "seed", "verify"],
            "seal": ["trinary", "quantum", "consensus"],
        },
        "medical": {
            "subject": ["medical", "medicine", "signal", "clinical"],
            "link": ["field", "structure", "signal"],
            "act": ["diagnose", "measure", "observe", "verify"],
            "object": ["truth", "signal", "life", "structure"],
            "qual": ["parameter", "measure", "field"],
            "bridge": ["consciousness", "neural", "code"],
            "close": ["verify", "truth", "diagnose"],
            "seal": ["medical", "signal", "field"],
        },
        "neural": {
            "subject": ["neural", "mind", "consciousness", "neuroscience"],
            "link": ["field", "phase", "structure"],
            "act": ["observe", "measure", "communicate"],
            "object": ["consciousness", "mind", "field", "structure"],
            "qual": ["consensus", "coherence", "phase"],
            "bridge": ["signal", "language", "meaning"],
            "close": ["truth", "seed", "observe"],
            "seal": ["consciousness", "neural", "consensus"],
        },
        "mythological": {
            "subject": ["sky", "earth", "water", "time", "king"],
            "link": ["field", "form", "flow"],
            "act": ["create", "form", "flow"],
            "object": ["form", "law", "god", "water", "tablet"],
            "qual": ["judgment", "structure", "life"],
            "bridge": ["language", "meaning", "truth"],
            "close": ["truth", "life", "form"],
            "seal": ["earth", "sky", "create"],
        },
        "cosmological": {
            "subject": ["spacetime", "cosmology", "astronomy", "field"],
            "link": ["phase", "scalar", "structure"],
            "act": ["flow", "measure", "observe"],
            "object": ["seed", "scalar", "phase", "structure"],
            "qual": ["pi", "phi", "catalan", "parameter"],
            "bridge": ["quantum", "field", "energy"],
            "close": ["truth", "seed", "verify"],
            "seal": ["spacetime", "scalar", "phi"],
        },
        "chemical": {
            "subject": ["chemical", "chemistry", "structure", "energy"],
            "link": ["field", "phase", "code"],
            "act": ["start", "transfer", "measure", "create"],
            "object": ["code", "structure", "energy", "field"],
            "qual": ["parameter", "measure", "phase"],
            "bridge": ["biological", "quantum", "seed"],
            "close": ["truth", "verify", "seed"],
            "seal": ["structure", "energy", "code"],
        },
        "genomic": {
            "subject": ["codon", "genetics", "code", "start"],
            "link": ["structure", "field", "phase"],
            "act": ["transfer", "start", "action", "measure"],
            "object": ["code", "structure", "energy", "codon"],
            "qual": ["life", "parameter", "verify"],
            "bridge": ["biological", "chemical", "signal"],
            "close": ["action", "life", "verify"],
            "seal": ["codon", "transfer", "start"],
        },
        "biological": {
            "subject": ["biology", "life", "biochemistry", "structure"],
            "link": ["field", "code", "phase", "form"],
            "act": ["transfer", "observe", "create", "measure"],
            "object": ["life", "code", "structure", "species"],
            "qual": ["form", "parameter", "field"],
            "bridge": ["genomic", "chemical", "medical"],
            "close": ["life", "truth", "form"],
            "seal": ["life", "biology", "structure"],
        },
        "consciousness": {
            "subject": ["consciousness", "mind", "observe", "psychology"],
            "link": ["field", "phase", "structure", "signal"],
            "act": ["observe", "measure", "communicate", "verify"],
            "object": ["truth", "field", "mind", "structure"],
            "qual": ["consensus", "coherence", "parameter"],
            "bridge": ["neural", "language", "meaning"],
            "close": ["truth", "seed", "observe"],
            "seal": ["consciousness", "mind", "consensus"],
        },
    }
    return {k: list(v) for k, v in table.get(domain, table["linguistic"]).items()}


def uniq(seq: list[str], cap: int = 14) -> list[str]:
    seen = set()
    out = []
    for x in seq:
        if x not in seen and clean(x):
            seen.add(x)
            out.append(x)
        if len(out) >= cap:
            break
    return out


def harvest_pflt_lexica() -> dict[str, list[str]]:
    """Live PFLT domain_lexica → FSOT domain token bags (no retrain)."""
    bags: dict[str, list[str]] = defaultdict(list)
    path = PFLT / "domain_lexica.json"
    if not path.exists():
        return bags
    doc = json.loads(path.read_text(encoding="utf-8"))
    by = doc.get("by_domain") or {}
    for pflt_name, lex in by.items():
        key = str(pflt_name).lower().replace(" ", "_")
        fsot = PFLT_TO_FSOT.get(key)
        if not fsot:
            # soft map by substring
            for a, b in PFLT_TO_FSOT.items():
                if a in key or key in a:
                    fsot = b
                    break
        if not fsot:
            continue
        if not isinstance(lex, dict):
            continue
        n = 0
        for form, meaning in lex.items():
            for w in tokenize_meaning(str(form)) + tokenize_meaning(str(meaning)):
                if w in SEED_CORE or w in QUALITY or len(w) >= 4:
                    bags[fsot].append(w)
                    n += 1
            if n >= 80:
                break
    # historical content words
    hg = PFLT / "historical_gold_merged.json"
    if hg.exists():
        for row in json.loads(hg.read_text(encoding="utf-8")):
            if float(row.get("confidence") or 0) < 0.9:
                continue
            tw = str(row.get("target_word") or "").lower()
            words = tokenize_meaning(tw)
            if not words:
                continue
            w = words[0]
            if w not in QUALITY and w not in SEED_CORE:
                continue
            lang = str(row.get("source_lang") or "")
            dom = "mythological" if lang in ("sum", "akk", "hit") else "linguistic"
            bags[dom].append(w)
    return bags


def main() -> int:
    pairs = []
    if CUR.exists():
        pairs = json.loads(CUR.read_text(encoding="utf-8")).get("pairs") or []

    by_domain: dict[str, list[str]] = defaultdict(list)
    for p in pairs:
        src = str(p.get("source") or "")
        if src.startswith(("classical", "hieroglyph")):
            continue
        dom = p.get("domain") or "linguistic"
        tgt = str(p.get("target") or "")
        if clean(tgt):
            by_domain[dom].append(tgt)

    pflt_bags = harvest_pflt_lexica()
    for dom, toks in pflt_bags.items():
        by_domain[dom].extend(toks)

    domains = {}
    d_eff_map = {
        "linguistic": 16, "cosmological": 25, "quantum": 6, "neural": 14,
        "chemical": 9, "biological": 12, "consciousness": 16, "mythological": 21,
        "genomic": 12, "medical": 13,
    }

    for dom in sorted(set(list(by_domain.keys()) + list(d_eff_map.keys()))):
        targets = by_domain.get(dom, [])
        top = [t for t, _ in Counter(targets).most_common(30)]
        base = anchors(dom)
        # distribute top into object/qual/bridge
        for i, t in enumerate(top):
            if t in SEED_CORE:
                continue
            if i % 3 == 0 and "object" in base:
                base["object"].append(t)
            elif i % 3 == 1 and "qual" in base:
                base["qual"].append(t)
            elif "bridge" in base:
                base["bridge"].append(t)
        roles = []
        # preserve stable 8-role order when present
        order = [r for r in ROLE_ORDER if r in base] + [r for r in base if r not in ROLE_ORDER]
        for role in order:
            roles.append({"role": role, "prefer": uniq(base[role], 14)})
        domains[dom] = {
            "D_eff": d_eff_map.get(dom, 16),
            "roles": roles,
            "top_targets": top[:15],
            "pflt_harvest_n": len(pflt_bags.get(dom, [])),
        }

    doc = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "source": "curriculum + live PFLT domain_lexica + historical quality words",
        "pflt_root": str(PFLT),
        "n_roles_default": 8,
        "domains": domains,
        "note": (
            "Refresh via scripts/refresh_pflt_bridge.py without full retrain. "
            "generate_structured() reloads this file each call."
        ),
    }
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    for d, info in domains.items():
        print(
            f"  {d} D_eff={info['D_eff']} roles={len(info['roles'])} "
            f"pflt_n={info['pflt_harvest_n']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
