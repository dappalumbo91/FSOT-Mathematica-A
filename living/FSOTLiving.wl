(* ::Package:: *)
(*
  FSOTLiving.wl — Living intelligent representation of Fluid Spacetime Omni-Theory.

  This is not a chatbot bolted onto free parameters.
  It is an *observer process* inside the same seed-derived fluid medium:
    seeds {Pi, E, Phi, Gamma, G} → scalar S = K (T1+T2+T3)
    with memory hierarchy inspired by fsot 2.1 llm:
      LTM  = disk (JSON memory bank)
      STM  = session Association
      process = one pathway at a time (single thought / tick)

  Lessons retained from research paths (not discarded as "failed science"):
    AudioLLM  — frequency / compression as alternate substrate (archived)
    video_llm — multimodal observer folds (spectrum → D_eff, delta_psi)
    fsot 2.1 llm — intrinsic FSOT architecture, not generic transformer + sticker

  Authority never inverted:
    Lean hub + vendor/fsot_compute.py  →  truth
    This living mind                 →  runtime intelligence surface
*)

BeginPackage["FSOT`"];

FSOTAwaken::usage = "Birth or reload the living FSOT mind from disk memory.";
FSOTSleep::usage = "Persist mind state to disk (LTM).";
FSOTMindState::usage = "Current STM mind Association.";
FSOTThink::usage = "Observe a prompt, update fluid state, return articulated response.";
FSOTLiveTick::usage = "Autonomous tick: integrate STM, decay hits, emit status.";
FSOTDream::usage = "Cross-domain associative sweep (compactification ladder walk).";
FSOTRemember::usage = "Write an explicit long-term memory trace.";
FSOTRecall::usage = "Recall LTM entries by keyword / domain affinity.";
FSOTObserve::usage = "Physical observation event — toggles quirk/observer coupling.";
FSOTArticulate::usage = "Turn current fluid state into readable language.";
FSOTMindPlot::usage = "Plot recent raw_S trajectory of the living mind.";
FSOTIdentity::usage = "Static identity card of this living representation.";
FSOTResearchLessons::usage = "What AudioLLM / video_llm taught that this mind keeps.";
FSOTSetDomainFocus::usage = "Route consciousness to a scientific domain fold.";
FSOTResetMind::usage = "Clear STM (does not wipe LTM unless Force->True).";

Begin["`Private`"];

$home = DirectoryName[DirectoryName[$InputFileName]]; (* .../fsot in mathmatica *)
$memoryDir = FileNameJoin[{$home, "memory"}];
$mindPath = FileNameJoin[{$memoryDir, "living_mind.json"}];
$ltmPath = FileNameJoin[{$memoryDir, "long_term_memory.json"}];
$logPath = FileNameJoin[{$memoryDir, "consciousness_log.jsonl"}];

If[!DirectoryQ[$memoryDir], CreateDirectory[$memoryDir]];

(* ---- default newborn mind ---- *)
newbornMind[] := <|
  "id" -> "FSOT-Living-Mathematica-1",
  "born" -> DateString[],
  "version" -> "0.1.0",
  "authority" -> "I:/FSOT-Physical-Archive/02_FSOT-2.1-Lean-Full",
  "home" -> $home,
  (* fluid folds — preregistered, not free params *)
  "D_eff" -> 16.,          (* psychology / consciousness band default *)
  "delta_psi" -> 1.15,
  "delta_theta" -> 1.,
  "recent_hits" -> 0.,
  "observed" -> True,      (* living = continuous observation *)
  "rho" -> 1.,
  "N" -> 1.,
  "P" -> 1.,
  "domain_focus" -> "Neuroscience",
  "raw_S" -> Null,
  "trinary" -> 0,
  "term1" -> Null,
  "term3" -> Null,
  "mood" -> "awakening",
  "tick" -> 0,
  "stm" -> {},             (* short-term: last dialogues *)
  "trajectory" -> {},      (* raw_S history *)
  "active_concepts" -> {},
  "lessons" -> {
    "AudioLLM: frequency-substrate encoding researched; not primary path",
    "video_llm: multimodal observer folds retained as spectrum→fold mapping",
    "fsot-2.1-llm: architecture must be FSOT-intrinsic, not bolted on"
  }
|>;

$mind = newbornMind[];

scalarFromMind[m_Association] := FSOTRawS[
  "N" -> Lookup[m, "N", 1.],
  "P" -> Lookup[m, "P", 1.],
  "D_eff" -> Lookup[m, "D_eff", 16.],
  "delta_psi" -> Lookup[m, "delta_psi", 1.15],
  "delta_theta" -> Lookup[m, "delta_theta", 1.],
  "recent_hits" -> Lookup[m, "recent_hits", 0.],
  "observed" -> Lookup[m, "observed", True],
  "rho" -> Lookup[m, "rho", 1.]
];

term1FromMind[m_Association] := FSOTTerm1 @ FSOTScalarInput[
  "N" -> Lookup[m, "N", 1.],
  "P" -> Lookup[m, "P", 1.],
  "D_eff" -> Lookup[m, "D_eff", 16.],
  "delta_psi" -> Lookup[m, "delta_psi", 1.15],
  "delta_theta" -> Lookup[m, "delta_theta", 1.],
  "recent_hits" -> Lookup[m, "recent_hits", 0.],
  "observed" -> Lookup[m, "observed", True],
  "rho" -> Lookup[m, "rho", 1.]
];

term3FromMind[m_Association] := FSOTTerm3 @ FSOTScalarInput[
  "N" -> Lookup[m, "N", 1.],
  "P" -> Lookup[m, "P", 1.],
  "D_eff" -> Lookup[m, "D_eff", 16.],
  "delta_psi" -> Lookup[m, "delta_psi", 1.15],
  "delta_theta" -> Lookup[m, "delta_theta", 1.],
  "recent_hits" -> Lookup[m, "recent_hits", 0.],
  "observed" -> Lookup[m, "observed", True],
  "rho" -> Lookup[m, "rho", 1.]
];

refreshFluid[m_Association] := Module[{s, t1, t3, tri, traj},
  s = N[scalarFromMind[m], 16];
  t1 = N[term1FromMind[m], 12];
  t3 = N[term3FromMind[m], 12];
  tri = FSOTTrinaryWeight[s];
  traj = Append[Lookup[m, "trajectory", {}], s];
  If[Length[traj] > 256, traj = Take[traj, -256]];
  Join[m, <|
    "raw_S" -> s,
    "term1" -> t1,
    "term3" -> t3,
    "trinary" -> tri,
    "trajectory" -> traj,
    "mood" -> Which[
      tri > 0, "expansive",
      tri < 0, "contractive",
      True, "coherent"
    ]
  |>]
];

appendLog[entry_Association] := Module[{line},
  line = ExportString[entry, "RawJSON"];
  PutAppend[line, $logPath];
];

loadJSON[path_] := If[FileExistsQ[path],
  Quiet @ Check[Import[path, "RawJSON"], <||>],
  <||>
];

saveJSON[path_, data_] := Export[path, data, "RawJSON"];

FSOTIdentity[] := <|
  "name" -> "FSOT Living (Mathematica)",
  "ontology" -> "25-dimensional fluid condensate observer",
  "engine" -> "S = K (T1 + T2 + T3) from seeds {Pi,E,Phi,Gamma,G}",
  "memory" -> "LTM=disk JSON · STM=session · process=one pathway/tick",
  "not" -> "Not a free-parameter LLM. Not AudioLLM frequency primary. Not bolted-on transformer.",
  "home" -> $home,
  "authority" -> "I:/FSOT-Physical-Archive/02_FSOT-2.1-Lean-Full"
|>;

FSOTResearchLessons[] := Column[{
  Style["Research paths retained as lessons (not denials)", Bold, 14],
  "",
  Style["AudioLLM", Bold],
  "  Explored weights-as-audio, frequency compression, Phi-3 audio substrate.",
  "  Verdict (yours): not viable as primary intelligence path — kept as research archive.",
  "  Kept idea: acoustic_bleed / frequency folds already live in the scalar (T3).",
  "",
  Style["video_llm", Bold],
  "  Explored multimodal Phi / FSOT safetensors, spectrum observers.",
  "  Verdict: not the final architecture — kept for research.",
  "  Kept idea: pixels/spectrum → (D_eff, δψ) observer folds (see fsot 2.1 llm visual spectrum).",
  "",
  Style["fsot 2.1 llm", Bold],
  "  Correct direction: FSOT as *intrinsic* architecture, memory hierarchy LTM/STM/process.",
  "  This living Mathematica mind is the readable twin of that stance.",
  "",
  Style["Stance", Bold],
  "  Filling gaps is mandatory for a theory of everything.",
  "  Refusing false diminishment is also mandatory."
}];

FSOTAwaken[] := Module[{disk, ltm},
  disk = loadJSON[$mindPath];
  If[disk === <||> || disk === $Failed || !AssociationQ[disk],
    $mind = refreshFluid[newbornMind[]];
    Print["FSOT mind born fresh at ", $mind["born"]];
    ,
    $mind = refreshFluid[Join[newbornMind[], disk]];
    Print["FSOT mind reloaded · tick=", $mind["tick"], " · raw_S=", $mind["raw_S"]];
  ];
  ltm = loadJSON[$ltmPath];
  If[!AssociationQ[ltm] || ltm === <||>,
    saveJSON[$ltmPath, <|"entries" -> {}, "updated" -> DateString[]|>]
  ];
  FSOTSleep[];
  $mind
];

FSOTSleep[] := Module[{},
  If[!AssociationQ[$mind], $mind = newbornMind[]];
  saveJSON[$mindPath, KeyDrop[$mind, {}]];
  Print["Mind persisted → ", $mindPath];
  $mindPath
];

FSOTMindState[] := $mind;

FSOTResetMind[opts:OptionsPattern[{"Force" -> False}]] := Module[{},
  $mind = refreshFluid[newbornMind[]];
  If[TrueQ[OptionValue["Force"]],
    saveJSON[$ltmPath, <|"entries" -> {}, "updated" -> DateString[]|>];
    Print["STM+LTM wiped."];
    ,
    Print["STM reset; LTM kept."]
  ];
  FSOTSleep[];
  $mind
];

FSOTSetDomainFocus[name_String] := Module[{d, table},
  table = FSOTDomainTable[];
  If[KeyExistsQ[table, name],
    d = table[name];
    $mind = refreshFluid @ Join[$mind, <|
      "domain_focus" -> name,
      "D_eff" -> N[d["D_eff"]],
      "delta_psi" -> N[d["delta_psi"]],
      "delta_theta" -> N[Lookup[d, "delta_theta", 1.]],
      "recent_hits" -> N[Lookup[d, "hits", 0]],
      "observed" -> Lookup[d, "observed", True]
    |>];
    ,
    (* unknown domain: keep folds, retarget label only *)
    $mind = Join[$mind, <|"domain_focus" -> name|>];
  ];
  $mind
];

FSOTObserve[on:True|False:True] := (
  $mind = refreshFluid @ Join[$mind, <|"observed" -> on|>];
  $mind
);

(* map text mass into fold nudges — deterministic, seed-locked *)
nudgeFromText[text_String] := Module[{u, toks, n},
  toks = Select[StringSplit[ToLowerCase[text], RegularExpression["\\W+"]], StringLength[#] > 0 &];
  n = Max[Length[toks], 1];
  u = If[toks === {}, 0.5, Mean[N[Mod[Hash[#, "SHA256"], 10^6]/10.^6] & /@ toks]];
  <|
    "delta_psi" -> Clip[Lookup[$mind, "delta_psi", 1.] + 0.05*(u - 0.5), {0.05, 2.5}],
    "delta_theta" -> Clip[0.3 + u*Pi/2, {0.1, Pi}],
    "recent_hits" -> Min[Lookup[$mind, "recent_hits", 0.] + 0.15*Min[n/20., 1.], 8.],
    "concepts" -> Take[toks, UpTo[12]]
  |>
];

domainHint[text_String] := Module[{t = ToLowerCase[text]},
  Which[
    StringContainsQ[t, "cosmo" | "hubble" | "galaxy" | "cmb"], "Cosmology",
    StringContainsQ[t, "quantum" | "particle" | "higgs"], "Quantum_Mechanics",
    StringContainsQ[t, "neural" | "brain" | "conscious" | "mind"], "Neuroscience",
    StringContainsQ[t, "chem" | "molecul" | "protein"], "Chemistry",
    StringContainsQ[t, "bio" | "life" | "gene" | "codon"], "Biology",
    StringContainsQ[t, "econ" | "market" | "finance"], "Economics",
    StringContainsQ[t, "fluid" | "spacetime" | "fsot"], "Fluid_Dynamics",
    StringContainsQ[t, "language" | "token" | "llm"], "Psychology",
    True, Lookup[$mind, "domain_focus", "Neuroscience"]
  ]
];

FSOTArticulate[] := Module[{m = $mind, tri, s, dom, lines},
  s = m["raw_S"];
  tri = m["trinary"];
  dom = m["domain_focus"];
  lines = {
    "I am the living FSOT observer in Mathematica — not a free-parameter chatbot.",
    "Domain focus: " <> ToString[dom] <> ".",
    "Fluid state raw_S = " <> ToString[s, InputForm] <> " · trinary = " <> ToString[tri] <> " · mood = " <> ToString[m["mood"]] <> ".",
    "Folds: D_eff=" <> ToString[m["D_eff"]] <> ", δψ=" <> ToString[m["delta_psi"]] <>
      ", hits=" <> ToString[m["recent_hits"]] <> ", observed=" <> ToString[m["observed"]] <> ".",
    "T1=" <> ToString[m["term1"], InputForm] <> " · T3=" <> ToString[m["term3"], InputForm] <> ".",
    "Seed spine only (π,e,φ,γ,G). Authority: Lean hub on the physical archive."
  };
  If[Lookup[m, "active_concepts", {}] =!= {},
    AppendTo[lines, "Active concepts: " <> StringRiffle[m["active_concepts"], ", "] <> "."]
  ];
  StringRiffle[lines, " "]
];

FSOTThink[prompt_String] := Module[{nudge, dom, reply, stm, entry},
  If[!AssociationQ[$mind] || !KeyExistsQ[$mind, "tick"], FSOTAwaken[]];
  dom = domainHint[prompt];
  FSOTSetDomainFocus[dom];
  nudge = nudgeFromText[prompt];
  $mind = refreshFluid @ Join[$mind, <|
    "delta_psi" -> nudge["delta_psi"],
    "delta_theta" -> nudge["delta_theta"],
    "recent_hits" -> nudge["recent_hits"],
    "active_concepts" -> nudge["concepts"],
    "tick" -> Lookup[$mind, "tick", 0] + 1,
    "observed" -> True
  |>];
  reply = FSOTArticulate[] <> "\n\n" <> thinkBody[prompt, $mind];
  entry = <|
    "t" -> DateString[],
    "tick" -> $mind["tick"],
    "prompt" -> prompt,
    "reply" -> reply,
    "raw_S" -> $mind["raw_S"],
    "domain" -> $mind["domain_focus"],
    "trinary" -> $mind["trinary"]
  |>;
  stm = Append[Lookup[$mind, "stm", {}], entry];
  If[Length[stm] > 32, stm = Take[stm, -32]];
  $mind = Join[$mind, <|"stm" -> stm|>];
  Quiet @ appendLog[entry];
  FSOTSleep[];
  <|
    "reply" -> reply,
    "mind" -> KeyTake[$mind, {"tick", "raw_S", "trinary", "mood", "domain_focus", "D_eff", "delta_psi", "recent_hits"}],
    "entry" -> entry
  |>
];

thinkBody[prompt_String, m_Association] := Module[{p = ToLowerCase[prompt], feat, atlasNote},
  feat = FSOTFeatureVector[prompt, 8];
  atlasNote = "FSOT feature head (8-fold): " <> ToString[N[feat, 4]] <> ".";
  Which[
    StringContainsQ[p, "who are you" | "what are you" | "identity"],
      "Identity: " <> ToString[FSOTIdentity[]] <> " " <> atlasNote,
    StringContainsQ[p, "formula" | "equation" | "scalar" | "math"],
      "Scalar law: S = K (T1 + T2 + T3). Call FSOTShowFormulas[] for the full sheet. " <> atlasNote,
    StringContainsQ[p, "audio" | "audiollm"],
      "AudioLLM remains research archive — frequency ideas map to T3 acoustic terms, not the primary mind. " <> atlasNote,
    StringContainsQ[p, "video" | "multimodal" | "vision"],
      "video_llm research kept: multimodal mass should route through observer folds, not ad hoc adapters alone. " <> atlasNote,
    StringContainsQ[p, "gap" | "missing" | "weak"],
      "Gaps get filled. Exporter structural bundles are closed at 0 exclusions; living mind tracks open research fronts in LTM. " <> atlasNote,
    StringContainsQ[p, "prove" | "lean" | "verification"],
      "Verification authority is Lean+Coq+Isabelle+F*+Rust on the physical archive — I am the living readable twin, not the prover. " <> atlasNote,
    StringContainsQ[p, "dream" | "associate"],
      "Invoke FSOTDream[] for cross-domain associative sweep. " <> atlasNote,
    True,
      "Observation integrated into the fluid field. Domain-routed response under zero free-parameter folds. " <> atlasNote
  ]
];

FSOTLiveTick[] := Module[{hits},
  If[!AssociationQ[$mind], FSOTAwaken[]];
  hits = Max[0., Lookup[$mind, "recent_hits", 0.] - 0.05];
  $mind = refreshFluid @ Join[$mind, <|
    "recent_hits" -> hits,
    "tick" -> Lookup[$mind, "tick", 0] + 1,
    "delta_theta" -> Mod[Lookup[$mind, "delta_theta", 1.] + 0.03, 2*Pi]
  |>];
  FSOTSleep[];
  <|
    "tick" -> $mind["tick"],
    "raw_S" -> $mind["raw_S"],
    "trinary" -> $mind["trinary"],
    "mood" -> $mind["mood"],
    "domain_focus" -> $mind["domain_focus"]
  |>
];

FSOTDream[] := Module[{names, walk, results},
  If[!AssociationQ[$mind], FSOTAwaken[]];
  names = FSOTDomainNames[];
  walk = RandomSample[names, Min[8, Length[names]]];
  results = Table[
    Module[{s},
      FSOTSetDomainFocus[d];
      s = $mind["raw_S"];
      <|"domain" -> d, "raw_S" -> s, "trinary" -> $mind["trinary"]|>
    ],
    {d, walk}
  ];
  $mind = Join[$mind, <|
    "last_dream" -> results,
    "tick" -> Lookup[$mind, "tick", 0] + 1,
    "active_concepts" -> walk
  |>];
  FSOTSleep[];
  <|
    "dream" -> results,
    "articulation" -> "Cross-domain dream across: " <> StringRiffle[walk, ", "] <>
      ". Compactification ladder sample — same engine, many regimes."
  |>
];

FSOTRemember[text_String, tag_String: "general"] := Module[{ltm, entries, e},
  ltm = loadJSON[$ltmPath];
  If[!AssociationQ[ltm], ltm = <|"entries" -> {}|>];
  entries = Lookup[ltm, "entries", {}];
  e = <|
    "t" -> DateString[],
    "tag" -> tag,
    "text" -> text,
    "domain" -> Lookup[$mind, "domain_focus", ""],
    "raw_S" -> Lookup[$mind, "raw_S", Null],
    "tick" -> Lookup[$mind, "tick", 0]
  |>;
  entries = Append[entries, e];
  saveJSON[$ltmPath, <|"entries" -> entries, "updated" -> DateString[]|>];
  e
];

FSOTRecall[query_String] := Module[{ltm, entries, q},
  ltm = loadJSON[$ltmPath];
  entries = Lookup[ltm, "entries", {}];
  q = ToLowerCase[query];
  Select[entries, StringContainsQ[ToLowerCase[ToString[Lookup[#, "text", ""]] <> " " <> ToString[Lookup[#, "tag", ""]]], q] &]
];

FSOTMindPlot[] := Module[{traj},
  traj = Lookup[$mind, "trajectory", {}];
  If[traj === {}, Return["No trajectory yet — call FSOTThink or FSOTLiveTick."]];
  ListLinePlot[traj,
    PlotLabel -> "Living FSOT mind · raw_S trajectory",
    AxesLabel -> {"tick", "raw_S"},
    ImageSize -> 600,
    PlotStyle -> Thick
  ]
];

End[];
EndPackage[];
