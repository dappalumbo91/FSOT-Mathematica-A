# Phase: Publication demo + PFLT slot prefers

## What this phase adds

1. **`data/domain_slot_prefers.json`** — per-domain role prefer lists built from quality curriculum + PFLT historical content words.
2. **Structured decode** merges static `DOMAIN_SLOTS` with those prefers (occupation order per organ).
3. **`scripts/publication_demo.py`** — one command: train → routing → free vs structured → microscope boards.
4. **Mathematica microscope** still reads `data/microscope/score_boards.json`.

## Run

```powershell
cd "I:\fsot in mathmatica"
python scripts\publication_demo.py
```

Or pieces:

```powershell
python scripts\build_domain_prefer_lists.py
python scripts\run_fsot_llm_python.py
```

## Mathematica (formula microscope)

```wolfram
Get["I:/fsot in mathmatica/FSOT/init.wl"]
FSOTMicroscopeLoad[]
FSOTMicroscopeStructured[]
FSOTMicroscopePlotParts[1]
FSOTLLMFormulaSheet[]
```

Lean remains the verification authority. Mathematica shows score parts and slot formulas. Python runs train/decode on this machine.
