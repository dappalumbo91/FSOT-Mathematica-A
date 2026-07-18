#!/usr/bin/env python3
"""Expand FSOT Mathematica LLM curriculum + vocab from PFLT gold banks."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PFLT = Path(r"C:\Users\damia\Desktop\pflt\data")
HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
OUT_CUR = DATA / "fsot_llm_curriculum.json"
OUT_VOCAB = DATA / "fsot_llm_vocab.json"
OUT_REPORT = DATA / "pflt_expand_report.json"

# Map PFLT / historical contexts → FSOT LLM domain folds
QUALITY_CONTENT = {
    "water","river","king","sky","earth","law","god","son","female","mount","man","house",
    "land","fire","day","time","life","word","name","hand","eye","heart","blood","stone",
    "tree","bird","fish","mother","father","city","road","gold","silver","wind","rain",
    "sun","moon","star","sea","food","bread","wine","horse","dog","ox","sheep","field",
}
LANG_DOMAIN = {
    "sum": "mythological",
    "akk": "mythological",
    "hit": "mythological",
    "grc": "linguistic",
    "la": "linguistic",
    "san": "linguistic",
    "ang": "linguistic",
    "en": "linguistic",
}

SCI_DOMAIN_MAP = {
    "biology": "biological",
    "biochemistry": "biological",
    "chemistry": "chemical",
    "quantum": "quantum",
    "quantum_mechanics": "quantum",
    "cosmology": "cosmological",
    "astronomy": "cosmological",
    "astrophysics": "cosmological",
    "neuroscience": "neural",
    "psychology": "consciousness",
    "medicine": "medical",
    "medical": "medical",
    "genetics": "genomic",
    "linguistics": "linguistic",
    "particle_physics": "quantum",
    "nuclear_physics": "quantum",
    "chemistry": "chemical",
}


def _norm_token(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^\w\-]+", "", s, flags=re.UNICODE)
    s = s.strip("_-")
    # require a letter start — drop glyph debris like "-dt"
    if not s or not re.match(r"^[a-z]", s):
        return ""
    return s[:48]


def _good_target(t: str) -> bool:
    if not t or len(t) < 2 or len(t) > 24:
        return False
    if not re.match(r"^[a-z][a-z0-9_]*$", t):
        return False
    # drop classical dictionary debris
    if t.startswith(("a_", "an_", "the_")):
        return False
    if t.count("_") > 2:
        return False
    return True


def _english_word(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").strip().lower()
    s = re.sub(r"[^a-z0-9_\s\-]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:40]


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def expand() -> dict:
    vocab: set[str] = {
        "<pad>",
        "<bos>",
        "<eos>",
        "<unk>",
        "the",
        "a",
        "of",
        "and",
        "to",
        "in",
        "is",
        "that",
        "for",
        "on",
        "with",
        "fluid",
        "spacetime",
        "omni",
        "theory",
        "fsot",
        "scalar",
        "seed",
        "domain",
        "quantum",
        "neural",
        "cosmo",
        "chemical",
        "biological",
        "consciousness",
        "translate",
        "observe",
        "collapse",
        "trinary",
        "consensus",
        "coherence",
        "language",
        "meaning",
        "structure",
        "energy",
        "field",
        "phase",
        "flow",
        "pi",
        "phi",
        "euler",
        "catalan",
        "proof",
        "lean",
        "truth",
        "measure",
        "zero",
        "free",
        "parameter",
        "prediction",
        "verify",
        "communicate",
        "medical",
        "signal",
        "code",
        "codon",
        "token",
        "mind",
        "living",
        "up",
        "down",
        "superposed",
        "yes",
        "no",
        "true",
        "false",
        "one",
        "two",
        "three",
        "many",
        "all",
        "none",
        "cause",
        "effect",
        "before",
        "after",
        "because",
        "therefore",
        "sky",
        "earth",
        "time",
        "create",
        "form",
        "transfer",
        "action",
        "start",
        "diagnose",
        "universal",
        "communicator",
        "proto",
        "historical",
        "genomic",
        "rosetta",
        "hieroglyph",
        "classical",
        "coverage",
        "semantic",
        "gloss",
        "water",
        "if",
        "judgment",
        "human",
        "being",
    }
    pairs: list[dict] = []
    stats = Counter()

    # --- seed pairs (core FSOT) ---
    seed_pairs = [
        ("linguistic", "fluid spacetime omni theory", "fsot"),
        ("linguistic", "translate meaning structure", "language"),
        ("linguistic", "zero free parameter", "seed"),
        ("linguistic", "proto fluid language communicate", "universal"),
        ("linguistic", "universal communicator translate", "communicate"),
        ("cosmological", "cosmo field phase flow", "spacetime"),
        ("quantum", "quantum measure collapse", "trinary"),
        ("neural", "neural consciousness observe", "mind"),
        ("chemical", "chemical structure energy", "code"),
        ("biological", "biological codon code start", "transfer"),
        ("consciousness", "living mind observe field", "consciousness"),
        ("mythological", "sky earth time create", "form"),
        ("genomic", "start transfer energy structure", "action"),
        ("medical", "medical signal measure truth", "diagnose"),
        ("linguistic", "verify lean proof truth", "proof"),
        ("quantum", "superposed up down", "collapse"),
        ("linguistic", "consensus coherence field", "structure"),
        ("cosmological", "seed pi phi euler catalan", "scalar"),
        ("linguistic", "before after cause effect", "therefore"),
        ("medical", "diagnose medical signal", "truth"),
    ]
    for dom, ctx, tgt in seed_pairs:
        pairs.append({"domain": dom, "context": ctx, "target": tgt, "source": "seed"})
        vocab.update(ctx.split())
        vocab.add(tgt)
        stats["seed"] += 1

    # --- historical gold (high confidence) ---
    hg_path = PFLT / "historical_gold_merged.json"
    if hg_path.exists():
        hg = load_json(hg_path)
        # Prefer tier A / high confidence; cap for trainability
        ranked = sorted(
            hg,
            key=lambda x: (-float(x.get("confidence") or 0), x.get("tier") != "A"),
        )
        seen_ctx = set()
        for row in ranked:
            conf = float(row.get("confidence") or 0)
            if conf < 0.85:
                continue
            src = _norm_token(str(row.get("source_word") or ""))
            tgt = _english_word(str(row.get("target_word") or ""))
            if not src or not tgt or " " in tgt and len(tgt.split()) > 3:
                # multi-word targets: take first content word
                parts = [p for p in tgt.split() if len(p) > 2]
                tgt = parts[0] if parts else tgt.replace(" ", "_")[:24]
            tgt = _norm_token(tgt).replace("-", "_")
            if not _good_target(tgt):
                continue
            # Linguistic diet: prefer content words; drop long classical proper-name glosses
            if tgt not in QUALITY_CONTENT and (
                len(tgt) > 10 or tgt.endswith(("ian", "ean", "ese", "ish")) and tgt not in QUALITY_CONTENT
            ):
                # still allow high-confidence short content
                if conf < 0.95 or len(tgt) > 8:
                    continue
            lang = str(row.get("source_lang") or "en")
            dom = LANG_DOMAIN.get(lang, "linguistic")
            # context: source form + optional gloss keywords
            gloss = str(row.get("gloss") or "")
            gloss_bits = re.findall(r"[A-Za-z]{3,}", gloss.lower())[:4]
            ctx_words = [src.replace("_", " ")] + gloss_bits
            ctx = " ".join(ctx_words)[:120]
            key = (ctx, tgt)
            if key in seen_ctx:
                continue
            seen_ctx.add(key)
            pairs.append(
                {
                    "domain": dom,
                    "context": ctx,
                    "target": tgt,
                    "source": f"historical_gold:{lang}",
                    "confidence": conf,
                }
            )
            vocab.add(tgt)
            for w in ctx.split():
                nw = _norm_token(w)
                if nw and nw.isascii():
                    vocab.add(nw)
            stats["historical_gold"] += 1
            if stats["historical_gold"] >= 800:
                break

    # --- classical lexicon sample (source → english) ---
    cl_path = PFLT / "classical_full_trained_lexicon.json"
    if cl_path.exists():
        cl = load_json(cl_path)
        n = 0
        for src, eng in cl.items():
            if n >= 600:
                break
            eng_w = _english_word(str(eng))
            if not eng_w or len(eng_w) < 2:
                continue
            # skip huge multiword
            parts = eng_w.split()
            tgt = _norm_token(parts[0])
            if not _good_target(tgt):
                continue
            # prefer simple content words for classical gold
            if len(parts) > 1 and len(parts[0]) <= 2:
                tgt = _norm_token(parts[1]) if len(parts) > 1 else tgt
            if not _good_target(tgt):
                continue
            ctx = f"classical ancient meaning {tgt}"
            pairs.append(
                {
                    "domain": "linguistic",
                    "context": ctx,
                    "target": tgt,
                    "source": "classical_lexicon",
                }
            )
            vocab.add(tgt)
            vocab.update(w for w in ctx.split() if _good_target(_norm_token(w)) or w in ctx.split())
            n += 1
            stats["classical"] += 1

    # --- hieroglyph concepts (english glosses) ---
    hi_path = PFLT / "hieroglyph_pflt_lexicon.json"
    if hi_path.exists():
        hi = load_json(hi_path)
        n = 0
        seen = set()
        for _k, gloss in hi.items():
            if n >= 250:
                break
            g = _english_word(str(gloss).replace("_", " "))
            parts = [p for p in g.split() if len(p) > 2]
            if not parts:
                continue
            tgt = _norm_token(parts[-1])
            if not _good_target(tgt) or tgt in seen:
                continue
            seen.add(tgt)
            ctx = "hieroglyph " + " ".join(parts[:3])
            pairs.append(
                {
                    "domain": "mythological",
                    "context": ctx,
                    "target": tgt,
                    "source": "hieroglyph",
                }
            )
            vocab.add(tgt)
            vocab.update(p for p in parts if p.isascii())
            n += 1
            stats["hieroglyph"] += 1

    # --- rosetta concepts ---
    ros_path = PFLT / "rosetta_concept_to_en.json"
    if ros_path.exists():
        ros = load_json(ros_path)
        for concept, eng in ros.items():
            tgt = _norm_token(_english_word(str(eng)))
            if not tgt:
                continue
            ctx = f"rosetta concept {concept.lower()} meaning"
            pairs.append(
                {
                    "domain": "linguistic",
                    "context": ctx,
                    "target": tgt,
                    "source": "rosetta",
                }
            )
            vocab.add(tgt)
            vocab.update(ctx.split())
            stats["rosetta"] += 1

    # --- domain lexica (scientific surface) ---
    dl_path = PFLT / "domain_lexica.json"
    if dl_path.exists():
        dl = load_json(dl_path)
        by_dom = dl.get("by_domain") or {}
        n = 0
        for dname, lex in by_dom.items():
            if n >= 500:
                break
            if not isinstance(lex, dict):
                continue
            dom_key = SCI_DOMAIN_MAP.get(dname.lower(), "linguistic")
            # take a few entries per domain
            taken = 0
            for form, meaning in lex.items():
                if taken >= 2:
                    break
                m = _norm_token(str(meaning).replace("_", " ").split()[0] if meaning else "")
                f = _english_word(str(form).replace("_", " "))
                if not m or not f:
                    continue
                # prefer ascii meaning tokens
                if not m.isascii():
                    continue
                ctx = f"{dname.replace('_', ' ')} {f}"
                pairs.append(
                    {
                        "domain": dom_key,
                        "context": ctx[:120],
                        "target": m,
                        "source": f"domain_lexica:{dname}",
                    }
                )
                vocab.add(m)
                for w in ctx.split():
                    nw = _norm_token(w)
                    if nw and nw.isascii() and len(nw) > 1:
                        vocab.add(nw)
                taken += 1
                n += 1
                stats["domain_lexica"] += 1

    # --- medical / genomic extras from global_safe if present ---
    if dl_path.exists():
        gs = (load_json(dl_path)).get("global_safe") or {}
        med_keys = [k for k in gs if any(x in str(k).lower() for x in ("med", "gene", "codon", "protein", "cell"))]
        for k in med_keys[:200]:
            m = _norm_token(str(gs[k]).replace("_", " ").split()[0])
            if not m or not m.isascii():
                continue
            ctx = str(k).replace("_", " ").lower()
            pairs.append(
                {
                    "domain": "medical" if "med" in ctx or "cell" in ctx else "genomic",
                    "context": ctx[:120],
                    "target": m,
                    "source": "global_safe",
                }
            )
            vocab.add(m)
            stats["global_safe"] += 1

    # Dedup pairs by (context, target)
    uniq = []
    seen = set()
    for p in pairs:
        key = (p["context"], p["target"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    pairs = uniq

    # Clean vocab: ascii-ish tokens for stable hashing embeds
    vocab_list = sorted(
        {
            v
            for v in vocab
            if v
            and (
                v.startswith("<")
                or (v.isascii() and re.match(r"^[a-z][a-z0-9_\-]*$", v) and _good_target(v))
            )
        },
        key=lambda x: (not x.startswith("<"), x),
    )
    # Keep specials first
    specials = [t for t in ["<pad>", "<bos>", "<eos>", "<unk>"] if t in vocab_list]
    rest = [t for t in vocab_list if t not in specials]
    # Cap vocab for first runnable training size (still large expansion)
    MAX_VOCAB = 2500
    if len(rest) > MAX_VOCAB - len(specials):
        # prefer tokens that appear as targets
        targets = Counter(p["target"] for p in pairs)
        rest = sorted(rest, key=lambda t: (-targets.get(t, 0), t))[: MAX_VOCAB - len(specials)]
    vocab_list = specials + rest

    # Drop pairs whose target not in vocab
    vset = set(vocab_list)
    pairs = [p for p in pairs if p["target"] in vset]

    cur = {
        "name": "FSOT multi-domain curriculum expanded from PFLT gold",
        "description": (
            "Contexts/targets from historical gold, classical lexicon, hieroglyph glosses, "
            "Rosetta concepts, and scientific domain lexica — plus FSOT seed pairs."
        ),
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "pflt_data_root": str(PFLT),
        "n_pairs": len(pairs),
        "pairs": pairs,
    }
    OUT_CUR.write_text(json.dumps(cur, indent=2, ensure_ascii=False), encoding="utf-8")

    vocab_doc = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "n": len(vocab_list),
        "tokens": vocab_list,
    }
    OUT_VOCAB.write_text(json.dumps(vocab_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "built_utc": cur["built_utc"],
        "n_pairs": len(pairs),
        "n_vocab": len(vocab_list),
        "by_source": dict(stats),
        "domains": dict(Counter(p["domain"] for p in pairs)),
        "curriculum": str(OUT_CUR),
        "vocab": str(OUT_VOCAB),
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    expand()
