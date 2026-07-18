#!/usr/bin/env python3
"""
FSOT Mathematica LLM — publication demo

Side-by-side: routing · free gen · structured slots · microscope boards.
Run after (or it will invoke) the train path lightly via import.

  python scripts/publication_demo.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
sys.path.insert(0, str(HOME / "scripts"))

DATA = HOME / "data"
OUT = DATA / "publication_demo_report.json"
MICRO = DATA / "microscope" / "score_boards.json"


def main() -> int:
    # Ensure prefer lists + model fresh enough
    from build_domain_prefer_lists import main as build_prefers

    build_prefers()

    # Prefer running full train if model missing; else load path via re-run modular pieces
    model_path = HOME / "memory" / "fsot_llm_model.json"
    print("=" * 72)
    print("FSOT LLM PUBLICATION DEMO")
    print("Home:", HOME)
    print("Authority: I:/FSOT-Physical-Archive/02_FSOT-2.1-Lean-Full")
    print("Mathematica role: formula microscope (not Lean replacement)")
    print("=" * 72)

    # Always retrain for reproducible demo numbers (same as run script)
    print("\n[1/4] Training domain-allocated FSOT LLM …")
    import run_fsot_llm_python as engine

    rc = engine.main()
    if rc != 0:
        print("Train/verify failed", file=sys.stderr)
        return rc

    # Reload microscope + build human report
    micro = json.loads(MICRO.read_text(encoding="utf-8")) if MICRO.exists() else {}
    run_rep = json.loads((DATA / "fsot_llm_run_report.json").read_text(encoding="utf-8"))

    print("\n[2/4] ROUTING (occupation space)")
    routes = []
    for prompt in [
        "fluid spacetime language translate",
        "spacetime galaxy hubble",
        "fluid communicate meaning",
        "quantum measure collapse",
        "medical signal diagnose",
    ]:
        d = engine.infer_domain(prompt)
        de = engine.DOMAIN_FOLDS[d]["D_eff"]
        routes.append({"prompt": prompt, "domain": d, "D_eff": de})
        print(f"  {prompt!r}\n    → {d}  (D_eff={de})")

    print("\n[3/4] FREE vs STRUCTURED")
    # Re-instantiate is heavy; use last report generations
    free = run_rep.get("generations") or micro.get("free_generations") or []
    structured = run_rep.get("structured_generations") or micro.get("structured_generations") or []
    print("\n  FREE (anti-cycle):")
    for g in free:
        print(f"    {g.get('prompt')!r}\n      [{g.get('domain')}] {g.get('generated')}")
    print("\n  STRUCTURED (6–8 role sentences + PFLT prefers):")
    for g in structured:
        roles = " | ".join(f"{s['role']}={s['token']}" for s in g.get("steps") or [])
        print(f"    {g.get('prompt')!r}")
        print(f"      [{g.get('domain')} D_eff={g.get('D_eff')}] tokens: {g.get('generated')}")
        if g.get("sentence"):
            print(f"      sentence: {g.get('sentence')}")
        print(f"      {roles}")

    print("\n[3b/4] PARAGRAPHS (6-sentence arc + Therefore/Thus/Hence)")
    # Re-smoke paragraphs from engine without full retrain path
    demo_paras: list = []
    try:
        import run_fsot_llm_python as eng
        vocab = None
        vp = DATA / "fsot_llm_vocab.json"
        if vp.exists():
            vocab = json.loads(vp.read_text(encoding="utf-8"))["tokens"]
        m = eng.FSOTLLM(dim=32, vocab=vocab)
        mp = HOME / "memory" / "fsot_llm_model.json"
        if mp.exists():
            doc = json.loads(mp.read_text(encoding="utf-8"))
            for k, v in (doc.get("embeddings") or {}).items():
                if "::" in k:
                    d, tok = k.split("::", 1)
                    m.emb[(d, tok)] = v
        for pr in [
            "proto fluid communicate",
            "quantum measure collapse",
            "medical signal diagnose",
            "fsot scalar seed domain",
        ]:
            para = m.generate_paragraph(pr, n_sentences=6, n_slots=8)
            demo_paras.append(para)
            print(f"\n  {pr!r} [{para['domain']}] n={para['n_sentences']} arc={' → '.join(para.get('arc') or [])}")
            print(f"  {para['paragraph']}")
            for s in para.get("steps") or []:
                mark = "→" if s.get("kind") == "connector" else "·"
                print(f"    {mark} ({s.get('phase')}/{s.get('kind')}) {s.get('sentence')}")
        # keep microscope paragraphs fresh when demo runs
        if MICRO.exists() and demo_paras:
            micro_live = json.loads(MICRO.read_text(encoding="utf-8"))
            micro_live["paragraphs"] = demo_paras
            forms = dict(micro_live.get("formulas") or {})
            forms["paragraph_v2"] = (
                "concat(structured_slots | connector Therefore/Thus/Hence + Phi fills); "
                "default arc length 6"
            )
            micro_live["formulas"] = forms
            MICRO.write_text(json.dumps(micro_live, indent=2), encoding="utf-8")
    except Exception as e:
        print("  paragraph section skipped:", e)

    print("\n[4/4] MICROSCOPE (score parts — Mathematica plots these)")
    boards = micro.get("score_boards") or []
    for b in boards[:5]:
        print(f"\n  prompt: {b['prompt']}")
        print(f"  domain={b['domain']} D_eff={b['D_eff']} pred={b['prediction']}")
        for c in b.get("compare") or []:
            parts = c.get("parts") or {}
            print(
                f"    {c['token']}: score={c.get('score')}  "
                f"hybrid={parts.get('hybrid')} aff={parts.get('aff')} prior={parts.get('prior')}"
            )

    demo = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "authority_ok": run_rep.get("authority_ok"),
        "train_steps": run_rep.get("train_steps"),
        "routes": routes,
        "free_generations": free,
        "structured_generations": structured,
        "paragraphs": [
            {
                "prompt": p["prompt"],
                "mode": p.get("mode"),
                "domain": p["domain"],
                "n_sentences": p.get("n_sentences"),
                "arc": p.get("arc"),
                "paragraph": p["paragraph"],
                "sentences": p["sentences"],
            }
            for p in demo_paras
        ],
        "microscope_boards": boards,
        "formulas": micro.get("formulas")
        or {
            "total": "0.55*cos + 0.45*trit_sim + sign + affinity + prior",
            "slot_decode": "argmax score + role_prefer - filled_ban",
            "eta": "|suction|*|poof|*|alpha|*|K|/(1+hits+|loss|)",
            "paragraph_v2": "concat(structured_slots | connector Therefore/Thus/Hence + Phi fills); default arc length 6",
        },
        "mathematica": {
            "load": 'Get["I:/fsot in mathmatica/FSOT/init.wl"]',
            "microscope": [
                "FSOTMicroscopeLoad[]",
                "FSOTMicroscopeCompare[1]",
                "FSOTMicroscopePlotParts[1]",
                "FSOTMicroscopeStructured[]",
                "FSOTMicroscopeParagraphs[]",
                "FSOTLLMFormulaSheet[]",
            ],
        },
        "paths": {
            "run_report": str(DATA / "fsot_llm_run_report.json"),
            "microscope": str(MICRO),
            "prefers": str(DATA / "domain_slot_prefers.json"),
            "model": str(HOME / "memory" / "fsot_llm_model.json"),
        },
    }
    OUT.write_text(json.dumps(demo, indent=2), encoding="utf-8")
    print("\n" + "=" * 72)
    print("DEMO COMPLETE  authority_ok=", demo["authority_ok"])
    print("Wrote", OUT)
    print("Mathematica microscope:")
    print('  Get["I:/fsot in mathmatica/FSOT/init.wl"]')
    print("  FSOTMicroscopeLoad[]; FSOTMicroscopePlotParts[1]; FSOTMicroscopeStructured[]; FSOTMicroscopeParagraphs[]")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
