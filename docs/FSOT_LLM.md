# FSOT Language Model (Mathematica)

## Mission

Build and run a **language-model-class AI** whose entire geometry is **FSOT-derived** and **checked against the FSOT verification stack** — so mathematical relationships stay **visible** (named operators, seed formulas, trace ledgers), not lost in anonymous float tensors.

This sits with:

| Project | Role |
|---------|------|
| **FSOT-2.1-Lean** | Theory + multi-domain verification authority |
| **PFLT** | Proto-Fluid Language Translator — **linguistics / universal communication** (goal: full coverage of language as fluid meaning) |
| **FSOT-GPU** | Consensus attention, collapse, CUDA path |
| **This package** | Mathematica LLM path — exact math surface + train/generate |

## Architecture

```
text
  → tokenize
  → embed  (each token = compactification-ladder RawS folds; domain S modulates)
  → phase rotation  (θ = 2·position)
  → collapse  (θ_coll = C_eff · P_var)
  → consensus attention  (trit_sim · coherence gate · causal; NO softmax/exp)
  → residual + fluid FFN  ((x + ReLU(x)/φ)/(1+1/φ))
  → next-token scores  (trit_sim(h_last, embed(tok)))
  → generate / train
```

### Learning

```
η = |suction| · |poof| · |α| · |K| / (1 + recent_hits + |loss|)
loss = 1 − trit_sim(h_last, embed(target))
embed[target] ← normalize(embed[target] + η (h − embed[target]))
```

No free Adam schedules. Same suction/poof/α/K family as the theory stack and FSOT-GPU training stance.

## Verification

```wolfram
FSOTLLMVerifyAuthority[]
```

Compares live Mathematica constants to `data/fsot_seeds_authority.json` (from the GPU/archive triangulation: `k_fsot`, `c_eff`, `p_var`, collapse threshold, etc.).

## Traceability

Every forward writes `llm/traces/last_forward_trace.json` with:

- domain folds  
- `S_context` and modulation formula  
- collapse threshold  
- coherence per key  
- gate definition  
- top token scores  
- train step η and loss when training  

That is the point of Mathematica here: **see the relationships**.

## API

| Function | Use |
|----------|-----|
| `FSOTLLMNew[]` | Birth model |
| `FSOTLLMTrain[pairs, epochs]` | Multi-domain curriculum |
| `FSOTLLMForward["..."]` | Forward + full trace |
| `FSOTLLMGenerate["...", n]` | Autoregressive generation |
| `FSOTLLMSetDomain["medical"]` | Domain routing |
| `FSOTLLMLastTrace[]` | Last math ledger |
| `FSOTLLMVerifyAuthority[]` | Seed parity |

## Curriculum

`data/fsot_llm_curriculum.json` — multi-domain pairs (linguistic, cosmological, quantum, neural, medical, genomic, mythological, …). Expand this as PFLT gold and domain catalogs grow; same fluid, more language surface.

## Run

```wolfram
Get["I:/fsot in mathmatica/FSOT/init.wl"]
FSOTLLMVerifyAuthority[]
FSOTLLMNew[]
cur = Import["I:/fsot in mathmatica/data/fsot_llm_curriculum.json","RawJSON"]["pairs"]
FSOTLLMTrain[cur, 5]
FSOTLLMGenerate["fluid spacetime communicate", 20]
FSOTLLMLastTrace[]
```

Or: `examples/FSOT_LLM_Train_Generate.wls`
