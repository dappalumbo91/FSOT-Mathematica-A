# FSOT Mathematica A

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**Fluid Spacetime Omni-Theory** as a Mathematica formula microscope, living observer mind, and FSOT-native language path — with Python parity for train/generate.

**License:** Apache License 2.0  
**Repo:** https://github.com/dappalumbo91/FSOT-Mathematica-A  

Local clone path (optional): `I:\fsot in mathmatica`  
Verification authority (separate archive): Lean / multi-prover hub + GPU seed triangulation

## What this is

1. **Readable mathematics** — seeds → constants → `S = K(T1+T2+T3)`  
2. **Living observer mind** — STM/LTM, domain routing, think/dream  
3. **FSOT language model** — embed, collapse, **consensus attention (no softmax)**, suction–poof train, generate, **math trace ledger**  
4. **Conversation + explain** — multi-turn dialogue with claim-bank substance (not empty occupation rhetoric)

Zero free parameters beyond seeds `{π, e, φ, γ, G}` on the FSOT spine. Every operator is named and traceable.

### Scientific continuity

Prior literature still teaches its regimes (Newtonian mechanics, relativity, Standard Model, …). FSOT unifies under a seed spine; it does **not** erase the path that led here. See `docs/SCIENTIFIC_CONTINUITY.md`.

---

## Clone

```bash
git clone https://github.com/dappalumbo91/FSOT-Mathematica-A.git
cd FSOT-Mathematica-A
```

## Quick start

### Mathematica / Wolfram

Adjust the path to your clone:

```wolfram
Get["/path/to/FSOT-Mathematica-A/FSOT/init.wl"]

(* Authority parity with shipped seed JSON *)
FSOTLLMVerifyAuthority[]

(* Language model *)
FSOTLLMNew[]
cur = Import["/path/to/FSOT-Mathematica-A/data/fsot_llm_curriculum.json", "RawJSON"]["pairs"]
FSOTLLMTrain[cur, 5]
FSOTLLMGenerate["fluid spacetime communicate language", 16]
FSOTLLMLastTrace[]
FSOTLLMFormulaSheet[]

(* Living mind *)
FSOTAwaken[]
FSOTThink["Universal fluid communication across domains."]

(* Formula twin *)
FSOTShowFormulas[]

(* Microscope after a Python export *)
FSOTMicroscopeLoad[]
FSOTMicroscopePlotParts[1]
FSOTMicroscopeStructured[]
FSOTMicroscopeParagraphs[]
FSOTMicroscopeConversation[]
```

**Why Mathematica:** `docs/WHY_MATHEMATICA.md` — formula microscope (not a Lean replacement). Python trains/runs without Wolfram Engine.

### Python (train / conversation)

```powershell
cd FSOT-Mathematica-A
python scripts/run_fsot_llm_python.py          # full train + microscope export
python scripts/fsot_conversation.py --smoke   # multi-turn demo
python scripts/fsot_conversation.py --chat    # interactive
python scripts/fsot_explain.py --once "Does FSOT replace relativity?" --deep
```

### PFLT bridge (refresh slot prefers, no full retrain)

Optional: if you have Desktop PFLT data paths configured in the scripts.

```powershell
python scripts/refresh_pflt_bridge.py
```

Ontology note: ad-hoc free params steer when direction is unknown; FSOT fixes direction via seeds + domain occupation — see `docs/AD_HOC_VS_ZERO_FREE.md`.

### Conversation notes

See `docs/CONVERSATION.md`. Explain mode uses `data/explanatory_pack.json` (claims first). Deep arcs use 6–8 step paragraph tissue when not answering how/why.
```powershell
python scripts/expand_fluency_curriculum.py --quick-train
python scripts/fsot_conversation.py --chat
```

Script (if Wolfram Engine installed):

```powershell
wolframscript -file "I:\fsot in mathmatica\examples\FSOT_LLM_Train_Generate.wls"
```

---

## Layout

```
I:\fsot in mathmatica\
  FSOT\           Scalar, domains, shared embeds, init
  llm\            FSOTLLM.wl — LLM engine + traces/
  living\         Living observer mind
  memory\         Persisted mind + model JSON
  data\           Seeds authority, curriculum, domain export
  examples\       Train/generate + living awaken scripts
  docs\           FSOT_LLM.md, LIVING_MIND.md
  bridge\         Desktop project links (PFLT, GPU, archive)
```

---

## How the pieces fit

| System | What FSOT does there |
|--------|----------------------|
| **Lean archive** | Multi-domain verification ledger |
| **PFLT** | Proto-Fluid Language Translator — linguistics and universal communication (full language surface is the goal) |
| **FSOT-GPU** | Collapse, consensus attention, CUDA, industry LM host |
| **This Mathematica home** | Same math, **visible** operators + LLM train/generate + living mind |

PFLT and this LLM path are aligned: domain folds, scalar modulation, no ad-hoc free-parameter core. Mathematica is where you **see** every relationship in the ledger.

---

## Verification

- `data/fsot_seeds_authority.json` — from GPU/archive kernel constants  
- `FSOTLLMVerifyAuthority[]` — live WL vs authority  
- Traces: `llm/traces/last_forward_trace.json`  

---

## Stance

Gaps in logic get filled. Applications are real work across domains. Recognition is an uphill battle; the stack is built to be **checkable** (GitHub, X, verification bundle) so finding it is a matter of time, not of diluting the theory.
