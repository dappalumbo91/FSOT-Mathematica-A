(* ::Package:: *)
(*
  FSOTML.wl — FSOT feature geometry helpers used by the full FSOT LLM.

  Full language-model path: llm/FSOTLLM.wl
  This file keeps compact embed / trinary utilities shared with living mind.
*)

BeginPackage["FSOT`"];

FSOTFeatureVector::usage = "FSOT feature vector from text or scalar-state Association.";
FSOTTrinaryWeight::usage = "Map activation to trinary {-1,0,+1} via seed thresholds.";
FSOTAttentionWeights::usage = "Phi-temperature weights + trinary readout over scalar states.";
FSOTEmbedToken::usage = "Token → FSOT compactification-ladder embedding (seed scalar folds).";
FSOTLanguageState::usage = "Update language-state Association under FSOT scalar dynamics.";
FSOTSmallLMStep::usage = "Next-token score step (delegates geometry; prefer FSOTLLM* for full path).";
FSOTMLExplain::usage = "Short pointer to full FSOT LLM architecture.";

Begin["`Private`"];

$thrLo = N[Sin[Pi/E] - 1];
$thrHi = N[(1 - Exp[-1])*1/Sqrt[2]];

FSOTTrinaryWeight[x_?NumericQ] := Which[
  x < $thrLo, -1,
  x > $thrHi, 1,
  True, 0
];

tokenUnit[s_String] := N[Mod[Hash[s, "SHA256"], 10^9]/10.^9];

FSOTEmbedToken[tok_String, dim_Integer: 16] := Module[
  {u, folds, base},
  u = tokenUnit[tok];
  folds = Table[
    FSOTRawS[
      "D_eff" -> N[3 + 2*i],
      "delta_psi" -> 0.35 + 0.9*u,
      "recent_hits" -> N[Mod[i, 3]],
      "observed" -> EvenQ[i],
      "delta_theta" -> N[u*Pi]
    ],
    {i, 0, dim - 1}
  ];
  base = N[folds];
  base/Max[Norm[base], 10.^-12]
];

FSOTFeatureVector[text_String, dim_Integer: 32] := Module[
  {tokens, emb},
  tokens = StringSplit[ToLowerCase[text], RegularExpression["\\W+"]];
  tokens = Select[tokens, StringLength[#] > 0 &];
  If[tokens === {}, Return[ConstantArray[0., dim]]];
  emb = Mean[FSOTEmbedToken[#, dim] & /@ tokens];
  N[emb]
];

FSOTFeatureVector[s_Association] := Module[
  {raw, t1, t3},
  raw = FSOTRawS[s];
  t1 = FSOTTerm1[s];
  t3 = FSOTTerm3[s];
  N[{raw, t1, t3, s["D_eff"]/25., s["delta_psi"], Boole[TrueQ[s["observed"]]]}]
];

FSOTAttentionWeights[states_List] := Module[
  {scores, tri, w, phiT, z, e},
  scores = FSOTRawS /@ states;
  tri = FSOTTrinaryWeight /@ scores;
  phiT = N[(1 + Sqrt[5])/2];
  z = N[scores]/phiT;
  e = Exp[z - Max[z]];
  w = e/Total[e];
  <|"scores" -> scores, "trinary" -> tri, "weights" -> w,
    "note" -> "Temperature = Phi; full LLM path uses consensus (no softmax) in FSOTLLM.wl"|>
];

FSOTLanguageState[state_Association, observation_Association] := Module[
  {merged, sNew},
  merged = Join[state, observation];
  sNew = FSOTRawS[merged];
  Join[merged, <|
    "raw_S" -> sNew,
    "trinary" -> FSOTTrinaryWeight[sNew],
    "term1" -> FSOTTerm1[merged],
    "term3" -> FSOTTerm3[merged]
  |>]
];

FSOTSmallLMStep[context_String, vocab_List, dim_Integer: 16] := Module[
  {ctx, scores},
  ctx = FSOTEmbedToken[StringJoin[Riffle[StringSplit[context], " "]], dim];
  scores = Table[
    <|"token" -> tok, "score" -> N[ctx . FSOTEmbedToken[tok, dim]],
      "trinary" -> FSOTTrinaryWeight[ctx . FSOTEmbedToken[tok, dim]]|>,
    {tok, vocab}
  ];
  Reverse @ SortBy[scores, #score &]
];

FSOTMLExplain[] := Column[{
  Style["FSOT ML geometry + full LLM", Bold, 14],
  "Shared embeds/trinary: this file.",
  "Full FSOT language model (consensus attention, train, generate, authority verify):",
  "  Get living stack via init.wl then FSOTLLMNew[] / FSOTLLMTrain / FSOTLLMGenerate",
  "  Docs: docs/FSOT_LLM.md · Math: FSOTLLMShowMath[]"
}];

End[];
EndPackage[];
