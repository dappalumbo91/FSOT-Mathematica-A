(* ::Package:: *)
(*
  FSOT Mathematica home loader — repo root of FSOT-Mathematica-A

  Get[FileNameJoin[{"<path to FSOT-Mathematica-A>", "FSOT", "init.wl"}]]
*)

Module[{dir, living, llm},
  dir = DirectoryName[$InputFileName];
  Get[FileNameJoin[{dir, "FSOTScalar.wl"}]];
  Get[FileNameJoin[{dir, "FSOTDomains.wl"}]];
  Get[FileNameJoin[{dir, "FSOTML.wl"}]];
  living = FileNameJoin[{ParentDirectory[dir], "living", "FSOTLiving.wl"}];
  If[FileExistsQ[living], Get[living]];
  llm = FileNameJoin[{ParentDirectory[dir], "llm", "FSOTLLM.wl"}];
  If[FileExistsQ[llm], Get[llm]];
  form = FileNameJoin[{ParentDirectory[dir], "llm", "FSOTLLMFormulas.wl"}];
  If[FileExistsQ[form], Get[form]];
  micro = FileNameJoin[{ParentDirectory[dir], "llm", "FSOTMicroscope.wl"}];
  If[FileExistsQ[micro], Get[micro]];
];

Print["════════════════════════════════════════════════════════════════"];
Print["  FSOT Mathematica — formula twin + living mind + FSOT LLM"];
Print["  Home: ", ParentDirectory[DirectoryName[$InputFileName]]];
Print["  Authority: FSOT-2.1-Lean (physical archive 02_FSOT-2.1-Lean-Full)"];
Print["════════════════════════════════════════════════════════════════"];
Print["  Math:   FSOTShowFormulas[], FSOTRawS[...], FSOTDomainAtlas[]"];
Print["  Living: FSOTAwaken[], FSOTThink[\"...\"], FSOTDream[]"];
Print["  LLM:    FSOTLLMNew[], FSOTLLMTrain[...], FSOTLLMGenerate[... ]"];
Print["  Trace:  FSOTLLMLastTrace[], FSOTLLMVerifyAuthority[]"];
Print["  See math: FSOTLLMFormulaSheet[], FSOTLLMScoreBreakdown[ctx,tok,dom]"];
Print["           FSOTLLMDomainRouteExplain[\"...\"], FSOTMicroscopeLoad[]"];
Print["           FSOTMicroscopePlotParts[1], FSOTMicroscopeStructured[]"];
Print["           FSOTMicroscopeParagraphs[]  (* 6-sentence arcs + connectors *)"];
Print["           FSOTMicroscopeConversation[] (* multi-turn dialogue export *)"];
Print["  Dialogue (Python): python scripts/fsot_conversation.py --smoke | --chat"];
