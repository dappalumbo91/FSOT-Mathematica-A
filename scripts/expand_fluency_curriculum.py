#!/usr/bin/env python3
"""
Expand curriculum + vocab with meaning-bearing fluent discourse pairs.

Does NOT retrain the full model by default — appends pairs so the next
train / quick-warm can absorb them. Optional --quick-train warms embeds.

  python scripts/expand_fluency_curriculum.py
  python scripts/expand_fluency_curriculum.py --quick-train
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
CUR = DATA / "fsot_llm_curriculum.json"
VOCAB = DATA / "fsot_llm_vocab.json"
REPORT = DATA / "fluency_expand_report.json"

# Discourse frames → target content (closed, seed-aligned)
FLUENT_FRAMES: list[tuple[str, str, str]] = [
    # (context phrase, target, domain)
    ("when the linguistic fold opens", "language", "linguistic"),
    ("language routes through domain occupation", "domain", "linguistic"),
    ("translate meaning into structure", "translate", "linguistic"),
    ("communicate universal fluid meaning", "communicate", "linguistic"),
    ("proto fluid tongue carries meaning", "proto", "linguistic"),
    ("zero free parameter architecture", "parameter", "linguistic"),
    ("seed spine holds the law", "seed", "linguistic"),
    ("scalar law is not free ranking", "scalar", "linguistic"),
    ("so the measure confirms the claim", "measure", "linguistic"),
    ("therefore consensus joins the field", "consensus", "linguistic"),
    ("in other words the proof settles", "proof", "linguistic"),
    ("as a result truth holds the seal", "truth", "linguistic"),
    ("building on what we just held", "structure", "linguistic"),
    ("staying with the same topic fold", "domain", "linguistic"),
    ("addressing that question directly", "verify", "linguistic"),
    ("from long term memory i hold", "seed", "linguistic"),
    ("across the domain of language", "language", "linguistic"),
    ("inside the fold of meaning", "meaning", "linguistic"),
    ("through the medium of fluid", "fluid", "linguistic"),
    ("under the law of the scalar", "scalar", "linguistic"),
    # quantum
    ("quantum measure collapses the state", "collapse", "quantum"),
    ("trinary consensus without softmax", "trinary", "quantum"),
    ("observation collapses the field", "observe", "quantum"),
    ("phase structure of the particle", "phase", "quantum"),
    ("under measure the quantum opens", "measure", "quantum"),
    ("as a result collapse meets measure", "collapse", "quantum"),
    # neural / consciousness
    ("neural consciousness observes the mind", "mind", "neural"),
    ("living mind observes the field", "consciousness", "consciousness"),
    ("awareness registers the signal", "observe", "consciousness"),
    ("cortex fires along the path", "neural", "neural"),
    # medical
    ("medical signal helps diagnose truth", "diagnose", "medical"),
    ("clinical measure of the patient field", "medical", "medical"),
    ("therapy routes through the signal", "measure", "medical"),
    # cosmological
    ("spacetime phase flow of cosmology", "spacetime", "cosmological"),
    ("galaxy field under hubble flow", "cosmology", "cosmological"),
    ("universe phase along the scalar", "phase", "cosmological"),
    # chemical / bio / genomic
    ("chemical structure carries energy", "energy", "chemical"),
    ("biological life starts the code", "life", "biological"),
    ("codon transfer starts the gene", "codon", "genomic"),
    ("protein code under genomic transfer", "transfer", "genomic"),
    # mythological / form
    ("sky earth time create form", "create", "mythological"),
    ("form emerges from earth and sky", "form", "mythological"),
    # connectors / discourse content
    ("therefore a joins b toward c", "therefore", "linguistic"),
    ("thus a and b hold consensus", "consensus", "linguistic"),
    ("hence a verifies b against seed", "verify", "linguistic"),
    ("the path settles when the seal holds", "seed", "linguistic"),
    ("hybrid free bridge fills the gap", "flow", "linguistic"),
    ("occupation skeleton stays the spine", "structure", "linguistic"),
    ("fluent surface is not free ranking", "language", "linguistic"),
    ("gpt class fluency is the surface goal", "communicate", "linguistic"),
    ("pflt aims at full universal communication", "universal", "linguistic"),
    ("lean archive remains the authority", "proof", "linguistic"),
    ("mathematica is the formula microscope", "formula", "linguistic"),
    ("domain inertia keeps the topic sticky", "domain", "linguistic"),
    ("ban pool stops clone spam across turns", "structure", "linguistic"),
    ("active concepts carry into the next turn", "meaning", "linguistic"),
    # medical skill pack (clinical turns)
    ("clinical measure of the patient field", "measure", "medical"),
    ("diagnose from the medical signal", "diagnose", "medical"),
    ("therapy routes through monitored response", "therapy", "medical"),
    ("vital markers under clinical observation", "clinical", "medical"),
    ("pathology assessed against seed truth", "truth", "medical"),
    ("recovery path under protocol measure", "medical", "medical"),
    ("patient symptom under medical diagnose", "patient", "medical"),
    ("lab marker signal for clinical assess", "signal", "medical"),
    ("treatment protocol monitors the response", "protocol", "medical"),
    ("healing care under medical risk", "care", "medical"),
    ("scan the vital pulse of the field", "vital", "medical"),
    ("disease marker routes into diagnose", "disease", "medical"),
]

# Extra surface words to ensure vocab coverage for bridges
EXTRA_VOCAB = [
    "when", "first", "opens", "routes", "through", "occupation", "into",
    "carries", "holds", "confirms", "settles", "building", "staying",
    "addressing", "question", "directly", "memory", "hold", "across",
    "inside", "medium", "under", "law", "state", "without", "softmax",
    "observation", "opens", "meets", "registers", "signal", "fires",
    "along", "path", "helps", "patient", "therapy", "galaxy", "hubble",
    "universe", "protein", "gene", "emerges", "joins", "toward",
    "aligned", "checked", "returns", "reads", "fills", "gap",
    "skeleton", "spine", "surface", "ranking", "class", "fluency",
    "goal", "aims", "full", "communication", "archive", "remains",
    "authority", "microscope", "inertia", "keeps", "topic", "sticky",
    "stops", "clone", "spam", "turns", "active", "concepts", "next",
    "finally", "holding", "together", "checked", "against", "result",
    "words", "other", "same", "just", "held", "what", "we",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick-train", action="store_true", help="Warm model embeds on new pairs")
    ap.add_argument("--steps", type=int, default=3, help="Train passes over new pairs")
    args = ap.parse_args()

    cur = json.loads(CUR.read_text(encoding="utf-8")) if CUR.exists() else {"pairs": []}
    pairs: list[dict] = list(cur.get("pairs") or [])
    existing = {(p.get("context"), p.get("target"), p.get("source")) for p in pairs}

    added = []
    for ctx, tgt, dom in FLUENT_FRAMES:
        key = (ctx, tgt, "fluency_discourse")
        if key in existing:
            continue
        row = {
            "domain": dom,
            "context": ctx,
            "target": tgt,
            "source": "fluency_discourse",
        }
        pairs.append(row)
        added.append(row)
        existing.add(key)

    cur["pairs"] = pairs
    cur["n_pairs"] = len(pairs)
    cur["fluency_expanded_utc"] = datetime.now(timezone.utc).isoformat()
    cur["name"] = cur.get("name") or "FSOT multi-domain curriculum"
    CUR.write_text(json.dumps(cur, indent=2), encoding="utf-8")

    # vocab
    if VOCAB.exists():
        vdoc = json.loads(VOCAB.read_text(encoding="utf-8"))
        toks = list(vdoc.get("tokens") or [])
    else:
        vdoc = {}
        toks = []
    seen = set(toks)
    v_added = []
    for w in EXTRA_VOCAB:
        w = w.lower().strip()
        if w and w not in seen and w.isalpha():
            toks.append(w)
            seen.add(w)
            v_added.append(w)
    for row in added:
        for w in (row["context"] + " " + row["target"]).split():
            w = w.lower().strip(".,;:")
            if w and w not in seen and w.isalpha() and 2 <= len(w) <= 24:
                toks.append(w)
                seen.add(w)
                v_added.append(w)
    vdoc["tokens"] = toks
    vdoc["n"] = len(toks)
    vdoc["fluency_expanded_utc"] = datetime.now(timezone.utc).isoformat()
    VOCAB.write_text(json.dumps(vdoc, indent=2), encoding="utf-8")

    train_log = []
    if args.quick_train and added:
        sys.path.insert(0, str(HOME / "scripts"))
        import run_fsot_llm_python as eng

        model = eng.FSOTLLM(dim=32, vocab=toks)
        # load existing embeds
        if eng.MODEL_OUT.exists():
            doc = json.loads(eng.MODEL_OUT.read_text(encoding="utf-8"))
            for k, v in (doc.get("embeddings") or {}).items():
                if "::" in k:
                    d, t = k.split("::", 1)
                    model.emb[(d, t)] = v
            for t, doms in (doc.get("token_domain_allocation") or {}).items():
                for d in doms:
                    model.allocate(t, d, as_target=False)
        for d in eng.DOMAIN_FOLDS:
            for t in eng.SEED_CORE:
                model.allocate(t, d, as_target=True)
        for _ in range(max(1, args.steps)):
            for row in added:
                log = model.train_step(row["context"], row["target"], domain=row["domain"])
                train_log.append(
                    {
                        "domain": row["domain"],
                        "target": row["target"],
                        "loss": log.get("loss"),
                        "eta": log.get("eta"),
                    }
                )
        model.save()
        print(f"Quick-train: {len(train_log)} steps → {eng.MODEL_OUT}")

    report = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "pairs_added": len(added),
        "vocab_added": len(v_added),
        "n_pairs_total": len(pairs),
        "n_vocab_total": len(toks),
        "quick_train": bool(args.quick_train),
        "train_steps": len(train_log),
        "sample_added": added[:8],
        "note": "fluency_discourse pairs = meaning-bearing frames for GPT-path surface",
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Added {len(added)} fluency pairs → {CUR}")
    print(f"Added {len(v_added)} vocab tokens → {VOCAB}")
    print(f"Report → {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
