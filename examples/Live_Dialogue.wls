(* Live_Dialogue.wls — fluid observer dialogue + microscope of Python conversation *)

Get["I:/fsot in mathmatica/FSOT/init.wl"];
FSOTAwaken[];

prompts = {
  "Route to cosmology and report your fluid state.",
  "Is FSOT a theory of everything or just a model?",
  "How should a language model be built if free parameters are the wrong architecture?",
  "Dream across domains and summarize what you felt.",
  "What gaps should we fill next?"
};

Do[
  Print["\n── USER ──\n", p];
  r = FSOTThink[p];
  Print["── FSOT LIVING ──\n", r["reply"]];
  Print["state: ", r["mind"]];
  ,
  {p, prompts}
];

Print["\nTrajectory length: ", Length[FSOTMindState[]["trajectory"]]];
Print["\nPrimary multi-turn dialogue is Python (structured + paragraph organs):"];
Print["  python scripts/fsot_conversation.py --smoke"];
Print["  python scripts/fsot_conversation.py --chat"];
Print["Then: FSOTMicroscopeLoad[]; FSOTMicroscopeConversation[]"];
(* If conversation export exists, open it in the microscope *)
Quiet @ Check[
  FSOTMicroscopeLoad[];
  Print["\n── CONVERSATION EXPORT ──"];
  Print[FSOTMicroscopeConversation[]];
  ,
  Print["(no conversation export yet — run fsot_conversation.py --smoke)"]
];
