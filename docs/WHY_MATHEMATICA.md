# Does Mathematica make remedies easier to see?

**Yes — for diagnosis and design of FSOT-native intelligence.**  
Not as a replacement for Lean verification or CUDA throughput, but as the **formula microscope**.

## What was hard in float soup

| Problem | Hidden in PyTorch/CUDA | Visible in Mathematica |
|---------|------------------------|-------------------------|
| Wrong top token | One float logit | `hybrid + sign + affinity + prior` parts |
| Wrong domain | Implicit router | Cue scores + D_eff of winner |
| Same score everywhere | Unit embeds all collapse | D_eff spine per domain occupation |
| Generation loops | Softmax temperature knobs | Explicit ban / n-gram penalties |
| Free Adam rates | Optimizer state | `η = \|suction\|·\|poof\|·\|α\|·\|K\|/(1+hits+\|loss\|)` |

## How we use it

```wolfram
Get["I:/fsot in mathmatica/FSOT/init.wl"]

FSOTLLMFormulaSheet[]

(* Why "communicate" beats "finance" on a prompt *)
FSOTLLMScoreBreakdown["proto fluid communicate", "communicate", "linguistic"]
FSOTLLMScoreBreakdown["proto fluid communicate", "finance", "linguistic"]

(* Wrong organ? *)
FSOTLLMDomainRouteExplain["fluid spacetime language translate"]
FSOTLLMDomainRouteExplain["spacetime galaxy hubble"]

(* Occupation geometry *)
MatrixPlot @ Partition[FSOTLLMEmbedDomain["fsot", "linguistic", 16], 4]

(* After python train — microscope on exported boards *)
FSOTMicroscopeLoad[]
FSOTMicroscopeCompare[1]
FSOTMicroscopePlotParts[1]      (* bar chart: hybrid/sign/aff/prior *)
FSOTMicroscopeStructured[]      (* domain slot decode strings *)
```

Python (`scripts/run_fsot_llm_python.py`) remains the **train/generate engine** on this machine (Wolfram may not be installed).  
Mathematica is where you **inspect the mathematics of each remedy** and keep formulas aligned with Lean/GPU seeds — not a Lean replacement; a microscope.


## Authority chain

```
Lean + cross-proof  →  what is true
GPU / Python LLM    →  what runs at scale on this PC
Mathematica         →  what you can see and correct by formula
```
