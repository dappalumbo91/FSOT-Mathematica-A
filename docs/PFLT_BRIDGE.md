# PFLT live lexica bridge (no full retrain)

## Point

Structured slot **prefer lists** can track live PFLT data without rebuilding embeddings.

```
Desktop\pflt\data\domain_lexica.json
Desktop\pflt\data\historical_gold_merged.json
        │
        ▼
scripts/build_domain_prefer_lists.py
        │
        ▼
data/domain_slot_prefers.json
        │
        ▼
generate_structured()  ← reloads prefers every call
```

Train (`run_fsot_llm_python.py` / `publication_demo.py`) still needed when you want **new embed geometry**. Prefer refresh is enough when PFLT gold grows and you want slot sentences to pick better role words.

## Commands

```powershell
cd "I:\fsot in mathmatica"

# Refresh prefers only + print 8-role sentences (loads existing model embeds if any)
python scripts\refresh_pflt_bridge.py

# Prefers only, no smoke
python scripts\refresh_pflt_bridge.py --no-smoke

# Full train + demo
python scripts\publication_demo.py
```

## Outputs

| File | Role |
|------|------|
| `data/domain_slot_prefers.json` | 8-role prefer lists per domain |
| `data/pflt_bridge_report.json` | Bridge audit |
| `data/microscope/score_boards.json` | Structured gens + paragraphs updated on smoke |

## Mathematica

```wolfram
Get["I:/fsot in mathmatica/FSOT/init.wl"]
FSOTMicroscopeLoad[]
FSOTMicroscopeStructured[]
FSOTMicroscopeParagraphs[]   (* 6-sentence arcs + Therefore/Thus/Hence *)
```
