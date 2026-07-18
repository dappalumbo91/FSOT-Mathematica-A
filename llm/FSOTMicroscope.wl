(* ::Package:: *)
(*
  FSOTMicroscope.wl — Load Python-exported score boards and visualize remedies.

  Get["I:/fsot in mathmatica/FSOT/init.wl"]
  Get["I:/fsot in mathmatica/llm/FSOTMicroscope.wl"]
  FSOTMicroscopeLoad[]
  FSOTMicroscopeCompare[1]   (* first board *)
  FSOTMicroscopePlotParts[1]
  FSOTMicroscopeStructured[]
  FSOTMicroscopeParagraphs[]  (* 6-sentence arcs + Therefore/Thus/Hence *)
*)

BeginPackage["FSOT`"];

FSOTMicroscopeLoad::usage = "Load data/microscope/score_boards.json into FSOT`Private`$micro.";
FSOTMicroscopeCompare::usage = "Table comparing two candidates on a board index.";
FSOTMicroscopePlotParts::usage = "BarChart of score parts for winner vs loser on a board.";
FSOTMicroscopeStructured::usage = "Show structured slot generations from export.";
FSOTMicroscopeParagraphs::usage = "Show paragraph_v2 arcs (6 sentences + Therefore/Thus/Hence connectors).";
FSOTMicroscopeConversation::usage = "Show multi-turn conversation export (STM dialogue turns).";
FSOTMicroscopeFormulas::usage = "Print formulas recorded in the export.";

Begin["`Private`"];

$home = DirectoryName[DirectoryName[$InputFileName]];
$microPath = FileNameJoin[{$home, "data", "microscope", "score_boards.json"}];
$micro = <||>;

FSOTMicroscopeLoad[path_String: ""] := Module[{p},
  p = If[path === "", $microPath, path];
  If[!FileExistsQ[p], Return[<|"ok" -> False, "path" -> p|>]];
  $micro = Import[p, "RawJSON"];
  <|
    "ok" -> True,
    "path" -> p,
    "n_boards" -> Length[Lookup[$micro, "score_boards", {}]],
    "n_structured" -> Length[Lookup[$micro, "structured_generations", {}]],
    "n_paragraphs" -> Length[Lookup[$micro, "paragraphs", {}]],
    "built" -> Lookup[$micro, "built_utc", Lookup[$micro, "prefers_refreshed_utc", None]]
  |>
];

FSOTMicroscopeFormulas[] := Lookup[$micro, "formulas", <||>];

FSOTMicroscopeCompare[i_Integer: 1] := Module[{b, c},
  If[$micro === <||>, FSOTMicroscopeLoad[]];
  b = $micro["score_boards"][[i]];
  c = b["compare"];
  Grid[{
    {"prompt", b["prompt"]},
    {"domain", b["domain"] <> "  D_eff=" <> ToString[b["D_eff"]]},
    {"prediction", b["prediction"]},
    {"S_context", b["S_context"]},
    {"", ""},
    {"token A", c[[1]]["token"], "score", c[[1]]["score"], "parts", c[[1]]["parts"]},
    {"token B", c[[2]]["token"], "score", c[[2]]["score"], "parts", c[[2]]["parts"]}
  }, Alignment -> Left, Frame -> All]
];

FSOTMicroscopePlotParts[i_Integer: 1] := Module[
  {b, c, keys, a, bb, va, vb},
  If[$micro === <||>, FSOTMicroscopeLoad[]];
  b = $micro["score_boards"][[i]];
  c = b["compare"];
  keys = {"hybrid", "sign", "aff", "prior"};
  a = Lookup[c[[1]]["parts"], #, 0.] & /@ keys;
  bb = Lookup[c[[2]]["parts"], #, 0.] & /@ keys;
  BarChart[
    {a, bb},
    ChartLabels -> {Placed[keys, Axis], None},
    ChartLegends -> {c[[1]]["token"], c[[2]]["token"]},
    PlotLabel -> Row[{b["prompt"], "  [", b["domain"], " D_eff=", b["D_eff"], "]"}],
    ImageSize -> 520,
    AxesLabel -> {None, "contribution"}
  ]
];

FSOTMicroscopeStructured[] := Module[{sg},
  If[$micro === <||>, FSOTMicroscopeLoad[]];
  sg = Lookup[$micro, "structured_generations", {}];
  Column[
    Function[g,
      Column[{
        Style[g["prompt"], Bold],
        Row[{"domain ", g["domain"], "  D_eff=", g["D_eff"]}],
        g["generated"],
        If[KeyExistsQ[g, "steps"] && ListQ[g["steps"]] && Length[g["steps"]] > 0 && KeyExistsQ[g["steps"][[1]], "role"],
          Row[Riffle[Row[{#["role"], "→", #["token"]}] & /@ g["steps"], " | "]],
          Nothing
        ]
      }, Spacings -> 0.3]
    ] /@ Select[sg, KeyExistsQ[#, "generated"] &],
    Spacings -> 1.2
  ]
];

(* Paragraph arc viewer — connectors highlighted (Therefore / Thus / Hence) *)
FSOTMicroscopeParagraphs[i_: All] := Module[
  {ps, pick, renderStep, renderPara},
  If[$micro === <||>, FSOTMicroscopeLoad[]];
  ps = Lookup[$micro, "paragraphs", {}];
  If[ps === {} || ps === None,
    Return[Style["No paragraphs in export — run: python scripts/refresh_pflt_bridge.py --smoke", Italic]]
  ];
  pick = Which[
    i === All, ps,
    IntegerQ[i] && 1 <= i <= Length[ps], {ps[[i]]},
    True, ps
  ];
  renderStep[s_Association | s_?AssociationQ] := Module[{kind, txt, lab},
    kind = Lookup[s, "kind", "sentence"];
    txt = Lookup[s, "sentence", ""];
    lab = Row[{
      Style[ToString[Lookup[s, "index", "?"]], Gray],
      " ",
      Style[Lookup[s, "phase", ""], Bold, If[kind === "connector", Darker@Blue, Black]],
      " / ",
      Style[kind, If[kind === "connector", Blue, Gray]]
    }];
    Column[{
      lab,
      If[kind === "connector",
        Style[txt, Blue, Bold, 12],
        Style[txt, 11]
      ]
    }, Spacings -> 0.15]
  ];
  renderPara[p_] := Module[{steps, arc},
    steps = Lookup[p, "steps", {}];
    arc = Lookup[p, "arc", {}];
    Column[{
      Style[Lookup[p, "prompt", ""], Bold, 13],
      Row[{
        "domain ", Lookup[p, "domain", "?"],
        "  D_eff=", Lookup[p, "D_eff", "?"],
        "  mode=", Lookup[p, "mode", "paragraph_v2"],
        "  n=", Lookup[p, "n_sentences", Length[Lookup[p, "sentences", {}]]]
      }],
      If[arc =!= {} && arc =!= None,
        Style[StringRiffle[ToString /@ arc, " → "], Gray, 10],
        Nothing
      ],
      Style[Lookup[p, "paragraph", ""], 11],
      Spacer[4],
      Column[renderStep /@ steps, Spacings -> 0.45, Frame -> True, FrameStyle -> LightGray, Background -> Lighter[Gray, 0.95]]
    }, Spacings -> 0.35]
  ];
  Column[renderPara /@ pick, Spacings -> 1.4]
];

(* Multi-turn conversation viewer — from conversations.json or score_boards *)
FSOTMicroscopeConversation[i_: All] := Module[
  {doc, turns, pick, convPath, renderTurn},
  If[$micro === <||>, FSOTMicroscopeLoad[]];
  doc = Lookup[$micro, "conversation", None];
  If[doc === None || doc === {},
    convPath = FileNameJoin[{$home, "data", "microscope", "conversations.json"}];
    If[FileExistsQ[convPath],
      doc = Import[convPath, "RawJSON"],
      Return[Style["No conversation export — run: python scripts/fsot_conversation.py --smoke", Italic]]
    ]
  ];
  turns = Lookup[doc, "turns", {}];
  If[turns === {} || turns === None,
    Return[Style["Conversation export has zero turns.", Italic]]
  ];
  pick = Which[
    i === All, turns,
    IntegerQ[i] && 1 <= i <= Length[turns], {turns[[i]]},
    True, turns
  ];
  renderTurn[t_] := Column[{
    Style[Row[{"tick ", Lookup[t, "tick", "?"], "  ·  ", Lookup[t, "mode", "?"], "  ·  ", Lookup[t, "domain", "?"], "  ·  mood=", Lookup[t, "mood", "?"]}], Bold, 11],
    Style["USER", Gray, 9],
    Style[Lookup[t, "user", ""], 12],
    Style["FSOT", Darker@Blue, 9],
    Style[Lookup[t, "reply", ""], 11],
    If[Lookup[t, "connectors", {}] =!= {} && Lookup[t, "connectors", {}] =!= None,
      Style["connectors: " <> StringRiffle[ToString /@ Lookup[t, "connectors", {}], " | "], Blue, 10],
      Nothing
    ],
    If[Lookup[t, "arc", {}] =!= {} && Lookup[t, "arc", {}] =!= None,
      Style[StringRiffle[ToString /@ Lookup[t, "arc", {}], " → "], Gray, 9],
      Nothing
    ]
  }, Spacings -> 0.2, Frame -> True, FrameStyle -> LightGray, Background -> Lighter[Gray, 0.96]];
  Column[{
    Style[Row[{"session ", Lookup[doc, "session_id", "?"], "  ·  n_turns=", Lookup[doc, "n_turns", Length[turns]]}], Bold, 13],
    Style[Lookup[doc, "formula", ""], Gray, 9],
    Spacer[6],
    Column[renderTurn /@ pick, Spacings -> 1.0]
  }, Spacings -> 0.4]
];

End[];
EndPackage[];
