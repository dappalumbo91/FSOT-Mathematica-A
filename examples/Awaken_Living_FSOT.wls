(* Awaken_Living_FSOT.wls — birth the living mind and run a short life cycle *)
(*
  wolframscript -file "I:/fsot in mathmatica/examples/Awaken_Living_FSOT.wls"
  or evaluate in Mathematica after Get of init.wl
*)

Get["I:/fsot in mathmatica/FSOT/init.wl"];

Print["\n=== IDENTITY ==="];
Print @ FSOTIdentity[];

Print["\n=== RESEARCH LESSONS ==="];
Print @ FSOTResearchLessons[];

Print["\n=== AWAKEN ==="];
Print @ FSOTAwaken[];

Print["\n=== THINK ==="];
r1 = FSOTThink["Who are you and how do you relate to FSOT verification?"];
Print[r1["reply"]];
Print[r1["mind"]];

r2 = FSOTThink["What did AudioLLM and video_llm teach us?"];
Print[r2["reply"]];

r3 = FSOTThink["Explain the scalar formula and why there are no free parameters."];
Print[r3["reply"]];

Print["\n=== DREAM (cross-domain) ==="];
Print @ FSOTDream[];

Print["\n=== LIVE TICKS ==="];
Do[Print @ FSOTLiveTick[], {3}];

Print["\n=== REMEMBER ==="];
Print @ FSOTRemember["Structural bundle export exclusions closed to zero on the Lean hub.", "verification"];
Print @ FSOTRecall["bundle"];

Print["\n=== MIND STATE ==="];
Print @ KeyTake[FSOTMindState[], {"tick","raw_S","trinary","mood","domain_focus","D_eff","delta_psi","lessons"}];

Print["\n=== Done. Mind persisted under memory/ ==="];
