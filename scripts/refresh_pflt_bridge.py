#!/usr/bin/env python3
"""
Refresh PFLT → FSOT slot prefers WITHOUT full model retrain.

Live lexica on Desktop PFLT are harvested into domain_slot_prefers.json.
Structured decode (generate_structured) reloads that file every call, so
slot sentences update immediately. Embeddings/train state stay as-is.

  python scripts/refresh_pflt_bridge.py
  python scripts/refresh_pflt_bridge.py --smoke   # also print sample sentences
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
sys.path.insert(0, str(HOME / "scripts"))

from build_domain_prefer_lists import main as build_prefers  # noqa: E402


def smoke_structured() -> list[dict]:
    """Structured gen only — no train. Uses existing model embeds if present."""
    import run_fsot_llm_python as eng

    vocab = None
    vp = DATA / "fsot_llm_vocab.json"
    if vp.exists():
        vocab = json.loads(vp.read_text(encoding="utf-8"))["tokens"]
    model = eng.FSOTLLM(dim=32, vocab=vocab)
    # warm seed/core allocation
    for d in eng.DOMAIN_FOLDS:
        for tok in eng.SEED_CORE:
            model.allocate(tok, d, as_target=True)

    # If trained embeds exist, load domain::token vectors
    mp = HOME / "memory" / "fsot_llm_model.json"
    if mp.exists():
        doc = json.loads(mp.read_text(encoding="utf-8"))
        emb = doc.get("embeddings") or {}
        for k, v in emb.items():
            if "::" in k:
                dom, tok = k.split("::", 1)
                model.emb[(dom, tok)] = v
        alloc = doc.get("token_domain_allocation") or {}
        for tok, doms in alloc.items():
            for d in doms:
                model.allocate(tok, d, as_target=False)
        print(f"  loaded embeds: {len(model.emb)} keys from model")

    prompts = [
        "fsot scalar seed domain",
        "proto fluid communicate",
        "neural consciousness observe",
        "medical signal measure",
        "quantum measure collapse",
        "sky earth time create",
        "start transfer energy structure",
        "cosmology spacetime field phase",
    ]
    out = []
    for pr in prompts:
        g = model.generate_structured(pr, n_slots=8)
        out.append(g)
        print(f"  [{g['domain']} D_eff={g['D_eff']}] {pr!r}")
        print(f"    tokens:   {g['generated']}")
        print(f"    sentence: {g.get('sentence', '')}")
        print(f"    roles:    " + " | ".join(f"{s['role']}={s['token']}" for s in g["steps"]))
    print("\n=== PARAGRAPH SMOKE (6-sentence arc + connectors) ===")
    paras = []
    for pr in prompts[:4]:
        p = model.generate_paragraph(pr, n_sentences=6, n_slots=8)
        paras.append(p)
        print(f"\n  {pr!r} [{p['domain']} D_eff={p['D_eff']}] mode={p.get('mode')} n={p['n_sentences']}")
        print(f"  arc: {' → '.join(p.get('arc') or [])}")
        print(f"  {p['paragraph']}")
        for s in p["steps"]:
            kind = s.get("kind", "sentence")
            mark = "→" if kind == "connector" else "·"
            print(f"    {mark} ({s['phase']}/{kind}/{s.get('focus','')}) {s['sentence']}")
    return out, paras


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh PFLT prefers without retrain")
    ap.add_argument("--smoke", action="store_true", help="Run structured gen samples after refresh")
    ap.add_argument("--no-smoke", action="store_true", help="Only rebuild prefers JSON")
    args = ap.parse_args()
    do_smoke = args.smoke or not args.no_smoke

    print("=== PFLT BRIDGE REFRESH (no full retrain) ===")
    print(f"PFLT data: C:\\Users\\damia\\Desktop\\pflt\\data")
    print(f"Out: {DATA / 'domain_slot_prefers.json'}")

    rc = build_prefers()
    prefers = json.loads((DATA / "domain_slot_prefers.json").read_text(encoding="utf-8"))

    report = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "prefer_refresh_only",
        "retrain": False,
        "prefers_path": str(DATA / "domain_slot_prefers.json"),
        "n_domains": len(prefers.get("domains") or {}),
        "domains": {
            d: {
                "D_eff": info.get("D_eff"),
                "n_roles": len(info.get("roles") or []),
                "pflt_harvest_n": info.get("pflt_harvest_n"),
                "roles": [r["role"] for r in (info.get("roles") or [])],
            }
            for d, info in (prefers.get("domains") or {}).items()
        },
        "note": (
            "generate_structured reloads domain_slot_prefers.json each call. "
            "Embeddings unchanged unless you run full publication_demo / run_fsot_llm_python."
        ),
    }

    samples: list[dict] = []
    paras: list[dict] = []
    if do_smoke:
        print("\n=== STRUCTURED SMOKE (8-role sentences) ===")
        samples, paras = smoke_structured()
        report["structured_samples"] = [
            {
                "prompt": g["prompt"],
                "domain": g["domain"],
                "D_eff": g["D_eff"],
                "generated": g["generated"],
                "sentence": g.get("sentence"),
                "roles": [{"role": s["role"], "token": s["token"]} for s in g["steps"]],
            }
            for g in samples
            if g.get("generated") is not None
        ]
        if paras:
            report["paragraphs"] = [
                {
                    "prompt": p["prompt"],
                    "mode": p.get("mode"),
                    "domain": p["domain"],
                    "D_eff": p["D_eff"],
                    "n_sentences": p.get("n_sentences"),
                    "arc": p.get("arc"),
                    "paragraph": p["paragraph"],
                    "sentences": p["sentences"],
                    "steps": [
                        {
                            "index": s.get("index"),
                            "phase": s.get("phase"),
                            "kind": s.get("kind"),
                            "focus": s.get("focus"),
                            "domain": s.get("domain"),
                            "sentence": s.get("sentence"),
                            "fills": s.get("fills"),
                        }
                        for s in (p.get("steps") or [])
                    ],
                    "formula": p.get("formula"),
                }
                for p in paras
            ]

    out = DATA / "pflt_bridge_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Refresh microscope: structured gens + paragraphs (clean, no _paragraphs blob)
    micro_path = DATA / "microscope" / "score_boards.json"
    if micro_path.exists() and (samples or paras):
        micro = json.loads(micro_path.read_text(encoding="utf-8"))
        if samples:
            micro["structured_generations"] = samples
        if paras:
            micro["paragraphs"] = [
                {
                    "prompt": p["prompt"],
                    "mode": p.get("mode"),
                    "domain": p["domain"],
                    "D_eff": p["D_eff"],
                    "n_sentences": p.get("n_sentences"),
                    "arc": p.get("arc"),
                    "paragraph": p["paragraph"],
                    "sentences": p["sentences"],
                    "steps": p.get("steps"),
                    "formula": p.get("formula"),
                    "ontology_note": p.get("ontology_note"),
                }
                for p in paras
            ]
        forms = dict(micro.get("formulas") or {})
        forms["paragraph_v2"] = (
            "concat(structured_slots | connector Therefore/Thus/Hence + Phi fills); "
            "default arc length 6"
        )
        micro["formulas"] = forms
        micro["prefers_refreshed_utc"] = report["built_utc"]
        micro_path.write_text(json.dumps(micro, indent=2), encoding="utf-8")
        print(f"\nUpdated microscope structured gens + paragraphs: {micro_path}")
        if paras:
            n_conn = sum(
                1
                for p in paras
                for s in (p.get("steps") or [])
                if s.get("kind") == "connector"
            )
            print(f"  paragraphs={len(paras)}  connector_lines={n_conn}")

    print(f"\nWrote {out}")
    print("Bridge refresh complete (retrain=False).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
