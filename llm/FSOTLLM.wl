(* ::Package:: *)
(*
  FSOTLLM.wl — Fluid Spacetime Omni-Theory language model (Mathematica)

  Full FSOT-derived LLM-class machine: tokenization, embedding geometry,
  collapse, trinary consensus attention (no softmax exp), residual path,
  suction–poof learning, generation, and a mathematical TRACE of every step.

  Authority:
    I:\FSOT-Physical-Archive\02_FSOT-2.1-Lean-Full
    GPU seeds (fsot_seeds_authority.json) — same K, C_eff, P_var, boot scalar
    Scalar twin: FSOT/FSOTScalar.wl

  Ontology (aligned with FSOT-GPU + PFLT + Lean):
    Seeds only. S = K (T1+T2+T3). Collapse threshold = C_eff * P_var.
    Consensus replaces softmax. Learning rate from suction/poof/alpha/K — not free Adam knobs.
    Every float is attached to a named FSOT quantity in the trace ledger.

  Author line: Damian Arthur Palumbo — FSOT applications across domains.
*)

BeginPackage["FSOT`"];

FSOTLLMNew::usage = "Create a new FSOT language model Association (seed-derived geometry).";
FSOTLLMLoad::usage = "Load model from memory/fsot_llm_model.json if present.";
FSOTLLMSave::usage = "Persist model + last trace to disk.";
FSOTLLMTokenize::usage = "Tokenize text to FSOT token list.";
FSOTLLMEmbed::usage = "Embed tokens → continuous fluid matrix [seq × dim].";
FSOTLLMCollapse::usage = "Collapse continuous values to trinary codes {0,1,2} via C_eff*P_var.";
FSOTLLMConsensusAttention::usage = "Consensus attention — no softmax/exp; traceable gates.";
FSOTLLMForward::usage = "Full forward pass with mathematical trace ledger.";
FSOTLLMGenerate::usage = "Autoregressive generation under FSOT scores.";
FSOTLLMTrainStep::usage = "One suction–poof fluid training step on (context → target) pairs.";
FSOTLLMTrain::usage = "Train over a curriculum Association list; returns history.";
FSOTLLMScoreNext::usage = "Score vocabulary candidates for next token given context.";
FSOTLLMSetDomain::usage = "Route model folds to a scientific/linguistic domain.";
FSOTLLMVerifyAuthority::usage = "Parity check model constants vs data/fsot_seeds_authority.json.";
FSOTLLMLastTrace::usage = "Most recent forward/train mathematical trace.";
FSOTLLMExplain::usage = "Architecture sheet — FSOT LLM vs free-parameter stacks.";
FSOTLLMShowMath::usage = "Print closed-form operators used in the LLM path (see also FSOTLLMFormulaSheet).";

Begin["`Private`"];

$home = DirectoryName[DirectoryName[$InputFileName]]; (* .../fsot in mathmatica *)
$modelPath = FileNameJoin[{$home, "memory", "fsot_llm_model.json"}];
$tracePath = FileNameJoin[{$home, "llm", "traces", "last_forward_trace.json"}];
$authPath = FileNameJoin[{$home, "data", "fsot_seeds_authority.json"}];

If[!DirectoryQ[FileNameJoin[{$home, "llm", "traces"}]],
  CreateDirectory[FileNameJoin[{$home, "llm", "traces"}]]
];

(* ---- seed geometry from live scalar package (symbolic roots) ---- *)
$phi = (1 + Sqrt[5])/2;
$gamma = N[EulerGamma, 40];
$gCat = N[Catalan, 40];
$alpha = Log[Pi]/(E*$phi^13);
$psiCon = 1 - Exp[-1];
$etaEff = 1/(Pi - 1);
$beta = 1/Exp[Pi^Pi + (E - 1)];
$gammaC = -Log[2]/$phi;
$omega = Sin[Pi/E]*Sqrt[2];
$thetaS = Sin[$psiCon*$etaEff];
$poof = Exp[(-Log[Pi]/E)/($etaEff*Log[$phi])];
$cEff = (1 - $poof*Sin[$thetaS])*(1 + 0.01*$gCat/(Pi*$phi));
$aBleed = Sin[Pi/E]*$phi/Sqrt[2];
$pVar = -Cos[$thetaS + Pi];
$bIn = $cEff*(1 - Sin[$thetaS]/$phi);
$aIn = $aBleed*(1 + Cos[$thetaS]/$phi);
$suction = $poof*(-Cos[$thetaS - Pi]);
$chaos = $gammaC/$omega;
$pNew = ($gamma/E)*Sqrt[2];
$cFactor = $cEff*$pNew;
$k = $phi*($gamma/E)*Sqrt[2]/Log[Pi]*0.99;
$collapse = N[$cEff*$pVar];  (* same operator as FSOT-GPU *)
fieldScale[dim_Integer: 32] := N[$phi/(Abs[$collapse]*Max[Sqrt[1./dim], 10.^-9])];

$llm = Null;
$lastTrace = <||>;

FSOTLLMShowMath[] := (If[NameQ["FSOT`FSOTLLMFormulaSheet"], FSOTLLMFormulaSheet[], Column[{
  "Load llm/FSOTLLMFormulas.wl for full remedy sheet",
 Column[{
  Style["FSOT LLM — Closed-form operators", Bold, 16],
  "",
  "Seeds: Pi, E, Phi=(1+Sqrt[5])/2, Gamma=EulerGamma, G=Catalan",
  "alpha = Log[Pi]/(E Phi^13)",
  "psi_con = 1 - Exp[-1]",
  "eta_eff = 1/(Pi-1)",
  "K = Phi (Gamma/E) Sqrt[2]/Log[Pi] * 0.99",
  "S = K (T1 + T2 + T3)   [FSOTRawS]",
  "",
  Style["LLM path", Bold, 13],
  "collapse_threshold θ_coll = C_eff * P_var",
  "collapse(x):  x>θ → SpinUp(+1);  x<-θ → SpinDown(-1);  else Superposed(0)",
  "trit_sim(a,b): mean match(+1)/opposite(-1)/superposed(0)",
  "consensus: gate = (coh(k)>1/2) ∧ causal;  out = (sim⊙gate)·V / |active|",
  "  — NO exp, NO softmax temperature free parameter",
  "phase: θ_i = 2 * position_i   (π-periodic fluid rotation)",
  "learning rate η = suction * poof * alpha * K / (1 + recent_hits + |loss|)",
  "embed_i = RawS folds on compactification ladder rungs D_eff = 3+2k",
  "",
  "Trace ledger names every quantity so relationships stay mathematical, not float soup."
}];

FSOTLLMExplain[] := Column[{
  Style["FSOT Language Model (Mathematica)", Bold, 16],
  "",
  "Purpose: a large-language-model-class intelligence path that is entirely FSOT-derived,",
  "verified against the FSOT verification stack (seeds/boot/scalar parity), and fully",
  "traceable in Mathematica so every relationship is visible.",
  "",
  "Aligned applications: PFLT (universal fluid communication / linguistics),",
  "FSOT-GPU (consensus attention, collapse, CUDA), Lean multi-domain ledger.",
  "",
  "Industry stack: free parameters, softmax exp, ad hoc schedules.",
  "FSOT stack: seeds, S, collapse, consensus, suction–poof learning, domain folds.",
  "",
  "Call: FSOTLLMNew[] · FSOTLLMTrain[curriculum] · FSOTLLMGenerate[prompt] · FSOTLLMLastTrace[]"
}];

defaultVocab[] := {
  "<pad>", "<bos>", "<eos>", "<unk>",
  "the", "a", "of", "and", "to", "in", "is", "that", "for", "on", "with",
  "fluid", "spacetime", "omni", "theory", "fsot", "scalar", "seed", "domain",
  "quantum", "neural", "cosmo", "chemical", "biological", "consciousness",
  "translate", "observe", "collapse", "trinary", "consensus", "coherence",
  "language", "meaning", "structure", "energy", "field", "phase", "flow",
  "pi", "phi", "euler", "catalan", "proof", "lean", "truth", "measure",
  "zero", "free", "parameter", "prediction", "verify", "communicate",
  "medical", "signal", "code", "codon", "token", "mind", "living",
  "up", "down", "superposed", "yes", "no", "true", "false",
  "one", "two", "three", "many", "all", "none",
  "cause", "effect", "before", "after", "because", "therefore",
  "sky", "earth", "time", "create", "form", "transfer", "action", "start",
  "diagnose", "universal", "communicator", "proto", "historical", "genomic",
  "rosetta", "hieroglyph", "classical", "coverage", "semantic", "gloss"
};

domainFolds = <|
  "linguistic" -> <|"D_eff" -> 16., "delta_psi" -> 0.8, "observed" -> True|>,
  "cosmological" -> <|"D_eff" -> 25., "delta_psi" -> 1.0, "observed" -> False|>,
  "quantum" -> <|"D_eff" -> 6., "delta_psi" -> 1.0, "observed" -> True|>,
  "neural" -> <|"D_eff" -> 14., "delta_psi" -> 0.7, "observed" -> True|>,
  "chemical" -> <|"D_eff" -> 9., "delta_psi" -> 0.5, "observed" -> True|>,
  "biological" -> <|"D_eff" -> 12., "delta_psi" -> 0.08, "observed" -> False|>,
  "consciousness" -> <|"D_eff" -> 16., "delta_psi" -> 1.15, "observed" -> True|>,
  "mythological" -> <|"D_eff" -> 21., "delta_psi" -> 1.0, "observed" -> True|>,
  "genomic" -> <|"D_eff" -> 12., "delta_psi" -> 0.5, "observed" -> False|>,
  "medical" -> <|"D_eff" -> 13., "delta_psi" -> 0.35, "observed" -> True|>
|>;

loadExternalVocab[] := Module[{path, doc},
  path = FileNameJoin[{$home, "data", "fsot_llm_vocab.json"}];
  If[!FileExistsQ[path], Return[None]];
  doc = Import[path, "RawJSON"];
  If[AssociationQ[doc] && KeyExistsQ[doc, "tokens"], doc["tokens"], None]
];

FSOTLLMNew[opts___Rule] := Module[
  {dim, vocab, o = Association[opts], emb, folds0, ext},
  dim = Lookup[o, "dim", 32];
  ext = loadExternalVocab[];
  vocab = Lookup[o, "vocab", If[ext === None, defaultVocab[], ext]];
  folds0 = Lookup[o, "domain", "linguistic"];
  emb = Association @@ Table[
    tok -> N[FSOTEmbedToken[tok, dim]],
    {tok, vocab}
  ];
  $llm = <|
    "id" -> "FSOT-LLM-Mathematica-1",
    "version" -> "1.0.0",
    "created" -> DateString[],
    "authority" -> "I:/FSOT-Physical-Archive/02_FSOT-2.1-Lean-Full",
    "dim" -> dim,
    "vocab" -> vocab,
    "vocab_index" -> Association @@ MapIndexed[#1 -> First[#2] &, vocab],
    "embeddings" -> emb,
    "domain" -> folds0,
    "folds" -> domainFolds[folds0],
    "recent_hits" -> 0.,
    "step" -> 0,
    "constants" -> <|
      "phi" -> N[$phi, 20],
      "gamma" -> N[$gamma, 20],
      "G" -> N[$gCat, 20],
      "alpha" -> N[$alpha, 20],
      "psi_con" -> N[$psiCon, 20],
      "eta_eff" -> N[$etaEff, 20],
      "beta" -> N[$beta, 20],
      "c_eff" -> N[$cEff, 20],
      "p_var" -> N[$pVar, 20],
      "poof" -> N[$poof, 20],
      "suction" -> N[$suction, 20],
      "c_factor" -> N[$cFactor, 20],
      "k" -> N[$k, 20],
      "collapse_threshold" -> N[$collapse, 20],
      "chaos" -> N[$chaos, 20]
    |>,
    "train_log" -> {},
    "note" -> "Zero free parameters beyond FSOT seeds; embeddings = seed scalar folds on tokens."
  |>;
  $llm
];

ensureModel[] := If[!AssociationQ[$llm], FSOTLLMNew[]];

FSOTLLMSetDomain[name_String] := Module[{},
  ensureModel[];
  If[KeyExistsQ[domainFolds, name],
    $llm = Join[$llm, <|"domain" -> name, "folds" -> domainFolds[name]|>],
    $llm = Join[$llm, <|"domain" -> name|>]
  ];
  $llm["domain"]
];

FSOTLLMTokenize[text_String] := Module[{toks},
  toks = StringSplit[ToLowerCase[text], RegularExpression["\\W+"]];
  Select[toks, StringLength[#] > 0 &]
];

tokenId[tok_String] := Module[{idx},
  ensureModel[];
  idx = $llm["vocab_index"];
  If[KeyExistsQ[idx, tok], idx[tok],
    If[KeyExistsQ[idx, "<unk>"], idx["<unk>"], 1]
  ]
];

embedOf[tok_String] := Module[{e},
  ensureModel[];
  e = $llm["embeddings"];
  If[KeyExistsQ[e, tok], e[tok],
    (* OOV: still FSOT-derived — never a random free vector *)
    N[FSOTEmbedToken[tok, $llm["dim"]]]
  ]
];

(* Domain allocation: embeds evaluated on active domain D_eff spine *)
FSOTLLMEmbed[tokens_List] := Module[{mat, folds, Sctx, trace, D0, i},
  ensureModel[];
  folds = $llm["folds"];
  Sctx = N[FSOTRawS[
    "D_eff" -> folds["D_eff"],
    "delta_psi" -> folds["delta_psi"],
    "observed" -> folds["observed"],
    "recent_hits" -> Lookup[$llm, "recent_hits", 0.]
  ], 16];
  mat = embedOf /@ tokens;
  (* Scale each row by domain fluid state — PFLT-style modulation by S *)
  mat = (# * (1 + Tanh[Sctx])) & /@ mat;
  trace = <|
    "op" -> "embed",
    "domain" -> $llm["domain"],
    "folds" -> folds,
    "S_context" -> Sctx,
    "S_formula" -> "S = K (T1+T2+T3) at domain folds",
    "modulation" -> "row_i := embed(token_i) * (1 + Tanh[S_context])",
    "seq_len" -> Length[tokens],
    "dim" -> $llm["dim"],
    "tokens" -> tokens
  |>;
  {mat, trace}
];

FSOTLLMCollapse[x_?NumericQ, scale_: Automatic] := Module[{sc, y},
  sc = If[scale === Automatic, fieldScale[32], scale];
  y = x*sc;
  Which[
    y > $collapse, 2,
    y < -$collapse, 0,
    True, 1
  ]
];

FSOTLLMCollapse[v_List, scale_: Automatic] := Module[{sc},
  sc = If[scale === Automatic, fieldScale[Max[Length[v], 1]], scale];
  FSOTLLMCollapse[#, sc] & /@ v
];

signedTrit[code_Integer] := Switch[code, 0, -1, 2, 1, _, 0];

coherenceOf[row_List] := Module[{codes, sharp},
  codes = FSOTLLMCollapse[row];
  sharp = Count[codes, c_ /; c =!= 1];
  N[sharp/Max[Length[codes], 1]]
];

tritSim[a_List, b_List] := Module[{ca, cb, n, acc, i, ta, tb, sc},
  sc = fieldScale[Max[Length[a], 1]];
  ca = FSOTLLMCollapse[#, sc] & /@ a;
  cb = FSOTLLMCollapse[#, sc] & /@ b;
  n = Min[Length[ca], Length[cb]];
  If[n == 0, Return[0.]];
  acc = 0;
  Do[
    ta = ca[[i]]; tb = cb[[i]];
    If[ta =!= 1 && tb =!= 1,
      acc += If[ta === tb, 1, -1]
    ],
    {i, n}
  ];
  N[acc/n]
];

phaseRotate[mat_List] := Module[{seq, dim, out, theta, cs, sn, k, a, b},
  seq = Length[mat];
  If[seq == 0, Return[{}]];
  dim = Length[mat[[1]]];
  out = mat;
  Do[
    theta = 2.* (i - 1);  (* π-periodic path: θ = 2·position *)
    cs = Cos[theta]; sn = Sin[theta];
    Do[
      a = out[[i, 2*k - 1]];
      b = If[2*k <= dim, out[[i, 2*k]], 0.];
      out[[i, 2*k - 1]] = cs*a - sn*b;
      If[2*k <= dim, out[[i, 2*k]] = sn*a + cs*b],
      {k, Floor[dim/2]}
    ],
    {i, seq}
  ];
  out
];

FSOTLLMConsensusAttention[q_List, k_List, v_List] := Module[
  {seq, sim, coh, gate, w, active, out, i, j, trace},
  seq = Length[q];
  sim = Table[tritSim[q[[i]], k[[j]]], {i, seq}, {j, seq}];
  coh = coherenceOf /@ k;
  (* causal + coherence gate > 1/2  (FSOT-GPU) *)
  gate = Table[
    If[j <= i && coh[[j]] > 0.5, sim[[i, j]], 0.],
    {i, seq}, {j, seq}
  ];
  active = Table[Max[Count[gate[[i]], x_ /; x != 0.], 1.], {i, seq}];
  out = Table[
    Sum[gate[[i, j]] * v[[j]], {j, seq}] / active[[i]],
    {i, seq}
  ];
  trace = <|
    "op" -> "consensus_attention",
    "formula" -> "out_i = Σ_j gate_ij V_j / |{j: gate_ij≠0}|",
    "gate" -> "causal ∧ (coherence(K_j) > 1/2) · trit_sim(Q_i,K_j)",
    "coherence_formula" -> "sharp_trits / dim  (collapse via θ_coll = C_eff P_var)",
    "collapse_threshold" -> N[$collapse, 16],
    "no_softmax" -> True,
    "no_exp" -> True,
    "seq" -> seq,
    "mean_coherence" -> Mean[coh],
    "active_frac" -> N[Mean[active]/seq],
    "coherence_per_key" -> coh,
    "sim_sample" -> If[seq >= 1, sim[[1]], {}]
  |>;
  {out, trace}
];

ffnFluid[mat_List] := Module[{},
  (* Parameter-light nonlinearity: ReLU with residual scale from Phi *)
  Table[
    Module[{row = mat[[i]], r},
      r = Map[Max[#, 0.] &, row];
      N[(row + r/$phi)/(1 + 1/$phi)]
    ],
    {i, Length[mat]}
  ]
];

FSOTLLMForward[text_String] := Module[
  {tokens, embT, emb, rot, attnT, attn, h, logits, scores, vocab, trace},
  ensureModel[];
  tokens = FSOTLLMTokenize[text];
  If[tokens === {}, tokens = {"<bos>"}];
  {emb, embT} = FSOTLLMEmbed[tokens];
  rot = phaseRotate[emb];
  {attn, attnT} = FSOTLLMConsensusAttention[rot, rot, rot];
  h = ffnFluid[Table[emb[[i]] + attn[[i]], {i, Length[emb]}]];
  vocab = $llm["vocab"];
  (* Next-token scores within domain allocation (+ universal) when set *)
  scores = Table[
    <|"token" -> tok, "score" -> tritSim[h[[-1]], embedOf[tok]],
      "S_tok" -> N[FSOTRawS[
        "D_eff" -> $llm["folds"]["D_eff"],
        "delta_psi" -> 0.5 + 0.5*Mean[embedOf[tok]],
        "observed" -> True
      ], 12]|>,
    {tok, vocab}
  ];
  scores = Reverse @ SortBy[scores, #score &];
  logits = scores;
  trace = <|
    "t" -> DateString[],
    "input" -> text,
    "tokens" -> tokens,
    "domain" -> $llm["domain"],
    "constants" -> $llm["constants"],
    "steps" -> {embT, <|
      "op" -> "phase_rotation",
      "formula" -> "θ_i = 2 * position_i; pair-wise rotation on dim"
    |>, attnT, <|
      "op" -> "ffn_fluid",
      "formula" -> "h = (x + ReLU(x)/Phi) / (1 + 1/Phi)"
    |>, <|
      "op" -> "next_token_scores",
      "formula" -> "score(tok) = trit_sim(h_last, embed(tok))",
      "top5" -> Take[scores, UpTo[5]]
    |>},
    "top_prediction" -> If[scores === {}, Null, scores[[1]]],
    "philosophy" -> "All operators seed-derived; ledger names every relationship."
  |>;
  $lastTrace = trace;
  Quiet @ Export[$tracePath, trace, "RawJSON"];
  <|
    "tokens" -> tokens,
    "hidden_last" -> h[[-1]],
    "scores" -> scores,
    "prediction" -> If[scores === {}, "<eos>", scores[[1, "token"]]],
    "trace" -> trace
  |>
];

FSOTLLMScoreNext[context_String, candidates_List: Automatic] := Module[
  {fwd, cand, last, sc},
  fwd = FSOTLLMForward[context];
  last = fwd["hidden_last"];
  cand = If[candidates === Automatic, $llm["vocab"], candidates];
  sc = Table[
    <|"token" -> t, "score" -> tritSim[last, embedOf[t]]|>,
    {t, cand}
  ];
  Reverse @ SortBy[sc, #score &]
];

FSOTLLMGenerate[prompt_String, nTokens_Integer: 16] := Module[
  {ctx, out, step, nxt, fwd, genTrace},
  ensureModel[];
  ctx = prompt;
  out = {};
  genTrace = {};
  Do[
    fwd = FSOTLLMForward[ctx];
    nxt = fwd["prediction"];
    If[nxt === "<eos>" || nxt === "<pad>", Break[]];
    AppendTo[out, nxt];
    AppendTo[genTrace, <|"step" -> step, "next" -> nxt, "top" -> Take[fwd["scores"], UpTo[3]]|>];
    ctx = ctx <> " " <> nxt,
    {step, nTokens}
  ];
  <|
    "prompt" -> prompt,
    "generated" -> StringRiffle[out, " "],
    "tokens" -> out,
    "domain" -> $llm["domain"],
    "trace_steps" -> genTrace,
    "full_last_trace" -> $lastTrace
  |>
];

(* suction–poof learning rate — FSOT-GPU training stance *)
learningRate[loss_?NumericQ, hits_?NumericQ] := Module[{eta},
  eta = N[Abs[$suction]*Abs[$poof]*Abs[$alpha]*Abs[$k]/(1. + hits + Abs[loss])];
  Max[eta, 10.^-8]
];

FSOTLLMTrainStep[context_String, target_String] := Module[
  {fwd, pred, loss, eta, hits, embT, eCtx, eTgt, delta, tok, newE, log},
  ensureModel[];
  fwd = FSOTLLMForward[context];
  pred = fwd["prediction"];
  (* Loss: 1 - trit_sim(h, target_embed) — geometric, not free CE temperature *)
  loss = 1. - tritSim[fwd["hidden_last"], embedOf[target]];
  hits = Lookup[$llm, "recent_hits", 0.];
  eta = learningRate[loss, hits];
  (* Fluid update on target token embedding toward hidden state *)
  eTgt = embedOf[target];
  delta = eta * (fwd["hidden_last"] - eTgt);
  newE = eTgt + delta;
  newE = newE/Max[Norm[newE], 10.^-12];
  $llm["embeddings"][target] = newE;
  (* Light update on context tokens: suction toward field mean *)
  Do[
    tok = t;
    If[KeyExistsQ[$llm["embeddings"], tok],
      eCtx = $llm["embeddings"][tok];
      $llm["embeddings"][tok] = Normalize[eCtx + 0.25*eta*(Mean[{eCtx, newE}] - eCtx)]
    ],
    {t, FSOTLLMTokenize[context]}
  ];
  $llm = Join[$llm, <|
    "recent_hits" -> Min[hits + 1., 64.],
    "step" -> Lookup[$llm, "step", 0] + 1
  |>;
  log = <|
    "step" -> $llm["step"],
    "context" -> context,
    "target" -> target,
    "prediction_before" -> pred,
    "loss" -> loss,
    "eta" -> eta,
    "eta_formula" -> "suction*poof*alpha*K/(1+hits+|loss|)",
    "hits" -> $llm["recent_hits"],
    "domain" -> $llm["domain"],
    "update" -> "embed[target] += eta (h_last - embed[target]); renormalize"
  |>;
  $llm["train_log"] = Append[Lookup[$llm, "train_log", {}], log];
  If[Length[$llm["train_log"]] > 500,
    $llm["train_log"] = Take[$llm["train_log"], -500]
  ];
  $lastTrace = Join[fwd["trace"], <|"train" -> log|>];
  log
];

FSOTLLMTrain[curriculum_List, epochs_Integer: 1] := Module[
  {hist = {}, e, row, r},
  ensureModel[];
  Do[
    Do[
      row = curriculum[[i]];
      r = FSOTLLMTrainStep[row["context"], row["target"]];
      If[KeyExistsQ[row, "domain"], FSOTLLMSetDomain[row["domain"]]];
      AppendTo[hist, r],
      {i, Length[curriculum]}
    ],
    {e, epochs}
  ];
  FSOTLLMSave[];
  <|
    "epochs" -> epochs,
    "steps" -> Length[hist],
    "final_loss_mean" -> If[hist === {}, 0., Mean[#loss & /@ Take[hist, -Min[20, Length[hist]]]]],
    "history_tail" -> Take[hist, -Min[10, Length[hist]]]
  |>
];

FSOTLLMLastTrace[] := $lastTrace;

FSOTLLMVerifyAuthority[] := Module[
  {auth, kc, report, pairs, ref, got, err},
  ensureModel[];
  If[!FileExistsQ[$authPath],
    Return[<|"ok" -> False, "reason" -> "missing fsot_seeds_authority.json", "path" -> $authPath|>]
  ];
  auth = Import[$authPath, "RawJSON"];
  kc = auth["kernel_constants"];
  pairs = {
    {"k", "k_fsot"},
    {"alpha", "alpha_fsot"},
    {"c_eff", "c_eff"},
    {"p_var", "p_var"},
    {"poof", "poof"},
    {"suction", "suction"},
    {"c_factor", "c_factor"}
  };
  report = Table[
    ref = kc[p[[2]]];
    got = $llm["constants"][p[[1]]];
    err = Abs[got - ref]/Max[Abs[ref], 10.^-15];
    <|"symbol" -> p[[1]], "authority_key" -> p[[2]], "ref" -> ref, "wl" -> got, "rel_err" -> err|>,
    {p, pairs}
  ];
  (* collapse threshold *)
  AppendTo[report,
    Module[{r = kc["c_eff"]*kc["p_var"], g = $llm["constants"]["collapse_threshold"]},
      <|"symbol" -> "collapse_threshold", "authority_key" -> "c_eff*p_var",
        "ref" -> r, "wl" -> g, "rel_err" -> Abs[g - r]/Max[Abs[r], 10.^-15]|>
    ]
  ];
  <|
    "ok" -> AllTrue[report, #rel_err < 10.^-6 &],
    "authority" -> $authPath,
    "boot_canonical" -> auth["boot"]["boot_scalar_canonical"],
    "rows" -> report,
    "note" -> "Verification against GPU/archive seed triangulation. Tight rel_err = stack agreement."
  |>
];

FSOTLLMSave[] := Module[{},
  ensureModel[];
  (* JSON-safe: drop huge train_log middle if needed — keep tail *)
  Export[$modelPath, $llm, "RawJSON"];
  If[$lastTrace =!= <||>, Export[$tracePath, $lastTrace, "RawJSON"]];
  $modelPath
];

FSOTLLMLoad[] := Module[{m},
  If[!FileExistsQ[$modelPath], Return[FSOTLLMNew[]]];
  m = Import[$modelPath, "RawJSON"];
  If[AssociationQ[m], $llm = m, FSOTLLMNew[]];
  $llm
];

End[];
EndPackage[];
