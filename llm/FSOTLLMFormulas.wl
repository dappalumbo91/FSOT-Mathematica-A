(* ::Package:: *)
(*
  FSOTLLMFormulas.wl — Visible mathematics for LLM remedies.

  Why Mathematica: every fix is a *named formula*, not an opaque hyperparameter.
  Load after FSOTScalar.wl / with init.wl.
*)

BeginPackage["FSOT`"];

FSOTLLMFormulaSheet::usage = "Full formula sheet: seeds, S, collapse, score, routing, generation remedies.";
FSOTLLMScoreBreakdown::usage = "Score candidate token given context tokens + domain folds — returns parts.";
FSOTLLMDomainRouteExplain::usage = "Show multi-cue domain scores for a prompt.";
FSOTLLMEmbedDomain::usage = "Domain D_eff-spine embedding of a token (occupation geometry).";

Begin["`Private`"];

$phi = (1 + Sqrt[5])/2;
$gamma = N[EulerGamma, 30];
$gCat = N[Catalan, 30];
$alpha = Log[Pi]/(E*$phi^13);
$psiCon = 1 - Exp[-1];
$etaEff = 1/(Pi - 1);
$cEff = Module[{poof, th},
  poof = Exp[(-Log[Pi]/E)/($etaEff*Log[$phi])];
  th = Sin[$psiCon*$etaEff];
  (1 - poof*Sin[th])*(1 + 0.01*$gCat/(Pi*$phi))
];
$pVar = Module[{th}, th = Sin[$psiCon*$etaEff]; -Cos[th + Pi]];
$collapse = N[$cEff*$pVar];
$poof = Exp[(-Log[Pi]/E)/($etaEff*Log[$phi])];
$suction = $poof*(-Cos[Sin[$psiCon*$etaEff] - Pi]);
$k = $phi*($gamma/E)*Sqrt[2]/Log[Pi]*0.99;

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

seedCore = {"fsot","fluid","spacetime","seed","scalar","domain","structure","energy",
  "field","phase","flow","translate","communicate","language","meaning","observe",
  "collapse","trinary","consensus","proof","truth","measure","verify","parameter",
  "theory","omni","universal","proto","diagnose","medical","mind","consciousness",
  "form","create","action","start","transfer","code","therefore","cause","effect",
  "water","sky","earth","king","river","law","god","life","pi","phi"};

tokenUnit[s_String] := N[Mod[Hash[s, "SHA256"], 10^9]/10.^9];

fieldScale[dim_:32] := N[$phi/(Abs[$collapse]*Max[Sqrt[1./dim], 10.^-9])];

FSOTLLMEmbedDomain[tok_String, domain_String:"linguistic", dim_Integer:16] := Module[
  {folds, u, D0, dp0, obs, vec, i, offset, dEff, dp, dt, s},
  folds = Lookup[domainFolds, domain, domainFolds["linguistic"]];
  u = tokenUnit[tok];
  D0 = folds["D_eff"]; dp0 = folds["delta_psi"]; obs = folds["observed"];
  vec = Table[
    offset = ((i + 0.5)/dim - 0.5)*(D0/2.);
    dEff = Max[3., Min[25., D0 + offset + 0.5*u]];
    dp = Max[0.05, Min[2.5, dp0*(0.75 + 0.5*u)]];
    dt = (u + i/dim)*(Pi/E);
    s = FSOTRawS[
      "D_eff" -> dEff, "delta_psi" -> dp, "delta_theta" -> dt,
      "observed" -> obs, "recent_hits" -> N[Mod[i, 3]]*u
    ];
    s*(1 + 0.2*Sin[2*Pi*u*$phi*(i + 1)]),
    {i, 0, dim - 1}
  ];
  N[vec/Norm[vec]]
];

cosine[a_List, b_List] := a.b/(Norm[a]*Norm[b] + 10.^-12);

tritSim[a_List, b_List] := Module[{sc, ca, cb, n, acc, i},
  sc = fieldScale[Length[a]];
  ca = Which[#*sc > $collapse, 2, #*sc < -$collapse, 0, True, 1] & /@ a;
  cb = Which[#*sc > $collapse, 2, #*sc < -$collapse, 0, True, 1] & /@ b;
  n = Min[Length[ca], Length[cb]];
  acc = 0;
  Do[
    If[ca[[i]] =!= 1 && cb[[i]] =!= 1,
      acc += If[ca[[i]] === cb[[i]], 1, -1]
    ],
    {i, n}
  ];
  N[acc/Max[n, 1]]
];

hybrid[a_List, b_List] := 0.55*cosine[a, b] + 0.45*tritSim[a, b];

FSOTLLMScoreBreakdown[context_String, candidate_String, domain_String:"linguistic"] := Module[
  {toks, folds, eCtx, eCand, last, sc, sCtx, sTok, signB, aff, prior, total},
  toks = Select[StringSplit[ToLowerCase[context], RegularExpression["\\W+"]], StringLength[#] > 0 &];
  folds = domainFolds[domain];
  eCtx = Mean[FSOTLLMEmbedDomain[#, domain] & /@ If[toks === {}, {"<bos>"}, toks]];
  eCand = FSOTLLMEmbedDomain[candidate, domain];
  sc = hybrid[eCtx, eCand];
  sCtx = FSOTRawS["D_eff" -> folds["D_eff"], "delta_psi" -> folds["delta_psi"], "observed" -> folds["observed"]];
  sTok = FSOTRawS["D_eff" -> folds["D_eff"], "delta_psi" -> folds["delta_psi"]*(0.5 + 0.5*tokenUnit[candidate]), "observed" -> folds["observed"]];
  signB = If[sTok*sCtx > 0, 0.04, -0.03];
  aff = If[MemberQ[toks, candidate], 0.28,
    If[AnyTrue[toks, StringLength[#] >= 4 && StringLength[candidate] >= 4 && StringTake[#, UpTo[4]] === StringTake[candidate, UpTo[4]] &], 0.10, 0.]];
  prior = 0.;
  If[MemberQ[seedCore, candidate], prior += 0.18];
  If[MemberQ[{"the","a","an","of","and","to","in","is"}, candidate], prior -= 0.55];
  total = sc + signB + aff + prior;
  <|
    "domain" -> domain,
    "D_eff" -> folds["D_eff"],
    "candidate" -> candidate,
    "total" -> N[total, 8],
    "formula" -> "total = 0.55 cos + 0.45 trit_sim + sign + affinity + prior",
    "parts" -> <|
      "hybrid" -> N[sc, 8],
      "cosine" -> N[cosine[eCtx, eCand], 8],
      "trit_sim" -> N[tritSim[eCtx, eCand], 8],
      "sign_bonus" -> signB,
      "affinity" -> aff,
      "prior" -> prior
    |>,
    "S_context" -> N[sCtx, 10],
    "S_tok" -> N[sTok, 10],
    "collapse_threshold" -> N[$collapse, 10],
    "note" -> "Same numeric magnitude of S can live in different D_eff occupation spaces."
  |>
];

FSOTLLMDomainRouteExplain[text_String] := Module[
  {t = ToLowerCase[text], scores, cues, soft},
  cues = {
    {"medical", 3.0, {"medical","diagnose","clinical","patient","disease"}},
    {"genomic", 3.0, {"codon","gene","dna","genome","protein"}},
    {"quantum", 3.0, {"quantum","collapse","particle","higgs","trinary"}},
    {"cosmological", 2.5, {"cosmo","galaxy","hubble","cmb","cosmology","universe"}},
    {"neural", 2.8, {"neural","brain","mind","consciousness"}},
    {"chemical", 2.5, {"chemical","molecule","bond","reaction"}},
    {"biological", 2.5, {"biology","life","species","organism"}},
    {"mythological", 2.2, {"sky","earth","create","sumer","hieroglyph","myth"}},
    {"consciousness", 2.0, {"observe","living","aware"}},
    {"linguistic", 3.2, {"translate","language","meaning","word","communicate","proto"}}
  };
  scores = Association[#[[1]] -> 0. & /@ cues];
  Do[
    scores[c[[1]]] += c[[2]]*Count[True][StringContainsQ[t, #] & /@ c[[3]]],
    {c, cues}
  ];
  If[StringContainsQ[t, "spacetime"], scores["cosmological"] += 1.0];
  If[scores["linguistic"] > 0 && scores["cosmological"] > 0 &&
      AnyTrue[{"language","translate","communicate","meaning","word","proto"}, StringContainsQ[t, #] &],
    scores["linguistic"] += 2.0; scores["cosmological"] *= 0.5
  ];
  If[StringContainsQ[t, "spacetime"] && !AnyTrue[{"cosmo","galaxy","hubble","cmb","universe"}, StringContainsQ[t, #] &],
    If[scores["linguistic"] > 0 || scores["neural"] > 0, scores["cosmological"] *= 0.35]
  ];
  <|
    "prompt" -> text,
    "scores" -> scores,
    "winner" -> First@Keys@TakeLargest[scores, 1],
    "D_eff" -> domainFolds[First@Keys@TakeLargest[scores, 1]]["D_eff"],
    "formula" -> "winner = argmax_d Σ w_d * cue_hits; language disambiguates soft spacetime"
  |>
];

FSOTLLMFormulaSheet[] := Column[{
  Style["FSOT LLM — Formula sheet (remedies visible)", Bold, 16],
  "",
  Style["1. Seeds (zero free parameters)", Bold, 13],
  "  Phi = (1+Sqrt[5])/2 , Gamma = EulerGamma , G = Catalan , Pi , E",
  "  alpha = Log[Pi]/(E Phi^13)",
  "  K = Phi (Gamma/E) Sqrt[2]/Log[Pi] * 0.99",
  "  S = K (T1 + T2 + T3)   ← FSOTRawS",
  "",
  Style["2. Occupation / domain (same magnitude ≠ same space)", Bold, 13],
  "  folds_d = {D_eff, delta_psi, observed}_d",
  "  embed(token | d): RawS along D_eff spine around folds_d[[D_eff]]",
  "  candidates_d = allocate(token→d) ∩ diet_cap(d) ∪ UNIVERSAL ∪ SEED_CORE",
  "",
  Style["3. Collapse & consensus (no softmax exp)", Bold, 13],
  "  θ_coll = C_eff * P_var",
  "  fieldScale = Phi / (θ_coll * sqrt(1/dim))",
  "  collapse(x) = SpinUp if x*scale>θ ; SpinDown if x*scale<-θ ; else Superposed",
  "  trit_sim = mean match(+1)/opposite(-1)/superposed(skip)",
  "  consensus gate = causal ∧ (coherence(K)>1/2)",
  "",
  Style["4. Score (remedy for bad top-1)", Bold, 13],
  "  hybrid = 0.55 cos(h, e_tok) + 0.45 trit_sim(h, e_tok)",
  "  sign = +0.04 if S_tok * S_ctx > 0 else -0.03   (same D_eff organ)",
  "  affinity = 0.28 if tok∈context else 0.10 prefix-match else 0",
  "  prior = +0.18 SEED_CORE ; -0.55 stopwords ; -0.40 noise",
  "  total = hybrid + sign + affinity + prior",
  "  → Call FSOTLLMScoreBreakdown[\"proto fluid communicate\", \"communicate\"]",
  "",
  Style["5. Routing (remedy for wrong organ)", Bold, 13],
  "  score_d = Σ w_cue * hits ; language boost when competing with soft spacetime",
  "  → FSOTLLMDomainRouteExplain[\"fluid spacetime language translate\"]",
  "",
  Style["6. Learning rate (suction–poof, not free Adam)", Bold, 13],
  "  η = |suction| |poof| |alpha| |K| / (1 + hits + |loss|)",
  "  loss = 1 - hybrid(h, embed(target|domain))",
  "",
  Style["7. Generation anti-cycle (remedy for stutter)", Bold, 13],
  "  score -= 2.5 if tok==last ; -= 1.8 if tok∈banned",
  "  score -= 2.2 if bigram repeat ; -= 2.8 if trigram repeat",
  "  score -= 0.35 * count(tok in generation)",
  "  D_eff(t) = D_eff0 + 0.15 Sin(2π Phi t/n)   (seed phase diversity)",
  "",
  Style["Why Mathematica helps", Bold, 13],
  "  Every remedy is a named term you can evaluate, plot, and audit.",
  "  Float soup in CUDA hides sign/affinity/prior; here the ledger shows them.",
  "",
  Style["Interactive checks", Bold, 13],
  "  FSOTLLMScoreBreakdown[\"medical signal diagnose\", \"diagnose\", \"medical\"]",
  "  FSOTLLMScoreBreakdown[\"medical signal diagnose\", \"finance\", \"medical\"]",
  "  FSOTLLMDomainRouteExplain[\"spacetime galaxy hubble\"]",
  "  FSOTLLMEmbedDomain[\"fsot\", \"linguistic\"] // MatrixPlot"
}];

End[];
EndPackage[];
