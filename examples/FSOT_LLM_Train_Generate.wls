(* FSOT_LLM_Train_Generate.wls
   Full pipeline: verify authority → train multi-domain curriculum → generate → dump math trace
*)

Get["I:/fsot in mathmatica/FSOT/init.wl"];

Print["\n======== FSOT LLM MATH SHEET ========"];
Print @ FSOTLLMShowMath[];

Print["\n======== AUTHORITY PARITY ========"];
v = FSOTLLMVerifyAuthority[];
Print[v["ok"]];
Print[v["rows"]];

Print["\n======== NEW MODEL ========"];
m = FSOTLLMNew[];
Print["dim=", m["dim"], " vocab=", Length[m["vocab"]], " collapseθ=", m["constants"]["collapse_threshold"]];

Print["\n======== LOAD CURRICULUM ========"];
cur = Import["I:/fsot in mathmatica/data/fsot_llm_curriculum.json", "RawJSON"];
pairs = cur["pairs"];
Print["pairs=", Length[pairs]];

Print["\n======== TRAIN (3 epochs) ========"];
hist = FSOTLLMTrain[pairs, 3];
Print[hist];

Print["\n======== FORWARD + TRACE ========"];
fwd = FSOTLLMForward["fluid spacetime language translate"];
Print["prediction=", fwd["prediction"]];
Print["top5=", Take[fwd["scores"], 5]];
Print["trace ops=", #["op"] & /@ fwd["trace"]["steps"]];

Print["\n======== GENERATE ========"];
g = FSOTLLMGenerate["fsot scalar seed domain", 12];
Print[g["generated"]];
Print[g["trace_steps"]];

Print["\n======== DOMAIN ROUTES ========"];
Do[
  FSOTLLMSetDomain[d];
  r = FSOTLLMForward["structure energy field"];
  Print[d, " → ", r["prediction"], "  S_ctx path in domain folds"],
  {d, {"linguistic", "quantum", "neural", "medical", "cosmological"}}
];

Print["\n======== LIVING MIND BRIDGE ========"];
If[NameQ["FSOT`FSOTThink"],
  FSOTAwaken[];
  Print @ FSOTThink["The FSOT language model trained on multi-domain curriculum."]["reply"]
];

Print["\n======== SAVED ========"];
Print @ FSOTLLMSave[];
Print["Trace file: I:/fsot in mathmatica/llm/traces/last_forward_trace.json"];
