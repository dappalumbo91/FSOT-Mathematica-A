(* ::Package:: *)
(*
  FSOTScalar.wl — Fluid Spacetime Omni-Theory scalar engine in Wolfram Language.

  Authority twin of vendor/fsot_compute.py and FSOT/Formal/Scalar.lean.
  Zero free parameters: every constant is derived from seeds {Pi, E, Phi, Gamma, G}.

  Usage (Mathematica / Wolfram Engine):
    Get["I:/FSOT-Physical-Archive/02_FSOT-2.1-Lean-Full/mathematica/FSOT/FSOTScalar.wl"]
    FSOT`BootScalar[]
    FSOT`RawS[<|"D_eff" -> 14, "delta_psi" -> 0.7, "observed" -> True|>]
*)

BeginPackage["FSOT`"];

FSOTSeeds::usage = "Association of foundational seeds {Pi, E, Phi, Gamma, G}.";
FSOTConstants::usage = "Association of all primary and composite derived constants.";
FSOTScalarInput::usage = "Build a scalar-input Association with FSOT defaults.";
FSOTTerm1::usage = "Observer-modulated base term T1.";
FSOTTerm2::usage = "Linear modulation term T2.";
FSOTTerm3::usage = "Valve-acoustic-phase term T3.";
FSOTRawS::usage = "Full scalar S = K*(T1+T2+T3). Alias: RawS.";
RawS::usage = "Alias for FSOTRawS.";
FSOTBootScalar::usage = "POC boot scalar at (D_eff=8, delta_psi=0.7, observed).";
FSOTShowFormulas::usage = "Print human-readable formula sheet for the scalar engine.";
FSOTParityCheck::usage = "Compare package constants against data/mathematica/fsot_authority_export.json if present.";

Begin["`Private`"];

(* ===== §1 Foundational seeds — no free parameters ===== *)
phi0 = (1 + Sqrt[5])/2;
gamma0 = N[EulerGamma, 50];
gCat0 = N[Catalan, 50];

FSOTSeeds[] := <|
  "Pi" -> Pi,
  "E" -> E,
  "Phi" -> phi0,
  "Gamma" -> gamma0,
  "G" -> gCat0
|>;

(* ===== §2 Layer 1 — primary derived constants ===== *)
alpha0 = Log[Pi]/(E*phi0^13);
psiCon0 = 1 - Exp[-1];  (* (E-1)/E *)
etaEff0 = 1/(Pi - 1);
beta0 = 1/Exp[Pi^Pi + (E - 1)];
gammaC0 = -Log[2]/phi0;
omega0 = Sin[Pi/E]*Sqrt[2];
thetaS0 = Sin[psiCon0*etaEff0];
poof0 = Exp[(-Log[Pi]/E)/(etaEff0*Log[phi0])];

(* ===== §3 Layer 2 — composite derived constants ===== *)
cEff0 = (1 - poof0*Sin[thetaS0])*(1 + 0.01*gCat0/(Pi*phi0));
aBleed0 = Sin[Pi/E]*phi0/Sqrt[2];
pVar0 = -Cos[thetaS0 + Pi];
bIn0 = cEff0*(1 - Sin[thetaS0]/phi0);
aIn0 = aBleed0*(1 + Cos[thetaS0]/phi0);
suction0 = poof0*(-Cos[thetaS0 - Pi]);
chaos0 = gammaC0/omega0;
pBase0 = gamma0/E;
pNew0 = pBase0*Sqrt[2];
cFactor0 = cEff0*pNew0;  (* consciousness factor *)
k0 = phi0*(gamma0/E)*Sqrt[2]/Log[Pi]*0.99;
cCosm0 = 1/(phi0*10);

FSOTConstants[] := <|
  "alpha" -> alpha0,
  "psi_con" -> psiCon0,
  "eta_eff" -> etaEff0,
  "beta" -> beta0,
  "gamma_c" -> gammaC0,
  "omega" -> omega0,
  "theta_s" -> thetaS0,
  "poof" -> poof0,
  "c_eff" -> cEff0,
  "a_bleed" -> aBleed0,
  "p_var" -> pVar0,
  "b_in" -> bIn0,
  "a_in" -> aIn0,
  "suction" -> suction0,
  "chaos" -> chaos0,
  "p_base" -> pBase0,
  "p_new" -> pNew0,
  "c_factor" -> cFactor0,
  "k" -> k0,
  "c_cosm" -> cCosm0
|>;

(* ===== §4 Scalar engine ===== *)
FSOTScalarInput[opts___Rule] := Module[{base},
  base = <|
    "N" -> 1.,
    "P" -> 1.,
    "D_eff" -> 25.,
    "delta_psi" -> 1.,
    "delta_theta" -> 1.,
    "recent_hits" -> 0.,
    "rho" -> 1.,
    "scale" -> 1.,
    "amplitude" -> 1.,
    "trend_bias" -> 0.,
    "observed" -> False
  |>;
  Join[base, Association[opts]]
];

FSOTTerm1[s_Association] := Module[
  {N, P, D, dp, hits, growth, base, t1},
  N = s["N"]; P = s["P"]; D = s["D_eff"]; dp = s["delta_psi"]; hits = s["recent_hits"];
  growth = Exp[alpha0*(1 - hits/N)*gamma0/phi0];
  base = (N*P/Sqrt[D])*Cos[(psiCon0 + dp)/etaEff0]*
    Exp[-alpha0*hits/N + s["rho"] + bIn0*dp]*(1 + growth*cEff0);
  t1 = base*(1 + pNew0*Log[D/25]);
  If[TrueQ[s["observed"]],
    t1 = t1*Exp[cFactor0*pVar0]*Cos[dp + pVar0]
  ];
  t1
];

FSOTTerm2[s_Association] := s["scale"]*s["amplitude"] + s["trend_bias"];

FSOTTerm3[s_Association] := Module[
  {N, P, D, dp, dt, valve, acoustic, phase},
  N = s["N"]; P = s["P"]; D = s["D_eff"]; dp = s["delta_psi"]; dt = s["delta_theta"];
  valve = beta0*Cos[dp]*(N*P/Sqrt[D])*(1 + chaos0*(D - 25)/25)*
    (1 + poof0*Cos[thetaS0 + Pi] + suction0*Sin[thetaS0]);
  acoustic = 1 + (aBleed0*Sin[dt]^2)/phi0 + (aIn0*Cos[dt]^2)/phi0;
  phase = 1 + bIn0*pVar0;
  valve*acoustic*phase
];

FSOTRawS[s_Association] := k0*(FSOTTerm1[s] + FSOTTerm2[s] + FSOTTerm3[s]);
FSOTRawS[opts___Rule] := FSOTRawS[FSOTScalarInput[opts]];
RawS = FSOTRawS;

FSOTBootScalar[] := FSOTRawS[
  "N" -> 1., "P" -> 1., "D_eff" -> 8., "delta_psi" -> 0.7,
  "recent_hits" -> 0., "observed" -> True, "rho" -> 1., "delta_theta" -> 1.
];

FSOTShowFormulas[] := Column[{
  Style["FSOT Scalar Engine — Formula Sheet", Bold, 16],
  "",
  Style["Seeds (zero free parameters)", Bold, 13],
  "  Phi = (1 + Sqrt[5])/2",
  "  Gamma = EulerGamma",
  "  G = Catalan",
  "  Pi, E = mathematical constants",
  "",
  Style["Layer 1", Bold, 13],
  "  alpha = Log[Pi]/(E Phi^13)",
  "  psi_con = 1 - Exp[-1]",
  "  eta_eff = 1/(Pi - 1)",
  "  beta = 1/Exp[Pi^Pi + (E - 1)]",
  "  gamma_c = -Log[2]/Phi",
  "  omega = Sin[Pi/E] Sqrt[2]",
  "  theta_s = Sin[psi_con eta_eff]",
  "  poof = Exp[(-Log[Pi]/E)/(eta_eff Log[Phi])]",
  "",
  Style["Layer 2", Bold, 13],
  "  c_eff = (1 - poof Sin[theta_s]) (1 + 0.01 G/(Pi Phi))",
  "  a_bleed = Sin[Pi/E] Phi/Sqrt[2]",
  "  p_var = -Cos[theta_s + Pi]",
  "  b_in = c_eff (1 - Sin[theta_s]/Phi)",
  "  a_in = a_bleed (1 + Cos[theta_s]/Phi)",
  "  suction = poof (-Cos[theta_s - Pi])",
  "  chaos = gamma_c/omega",
  "  p_new = (Gamma/E) Sqrt[2]",
  "  c_factor = c_eff p_new   (* consciousness *)",
  "  K = Phi (Gamma/E) Sqrt[2]/Log[Pi] * 0.99",
  "",
  Style["Scalar", Bold, 13],
  "  S = K (T1 + T2 + T3)",
  "  T1 = observer-modulated base (growth, perceived adjust, quirk if observed)",
  "  T2 = scale*amplitude + trend_bias",
  "  T3 = valve * acoustic * phase",
  "",
  Style["This is a compact, readable twin of the Lean/Python authority — not a replacement prover.", Italic]
}];

FSOTParityCheck[jsonPath_String: ""] := Module[
  {path, data, const, report, keys, ref, got, err},
  path = If[jsonPath === "",
    FileNameJoin[{DirectoryName[$InputFileName], "..", "..", "data", "mathematica", "fsot_authority_export.json"}],
    jsonPath
  ];
  If[!FileExistsQ[path], Return[<|"ok" -> False, "reason" -> "missing export JSON", "path" -> path|>]];
  data = Import[path, "RawJSON"];
  const = data["constants"];
  keys = {"alpha", "psi_con", "eta_eff", "beta", "c_eff", "k", "c_factor", "poof", "chaos"};
  report = Table[
    ref = const[k];
    got = N[FSOTConstants[][k], 20];
    err = Abs[got - ref]/Max[Abs[ref], 10.^-15];
    <| "key" -> k, "ref" -> ref, "wl" -> got, "rel_err" -> err |>,
    {k, keys}
  ];
  <|
    "ok" -> AllTrue[report, #["rel_err"] < 10.^-8 &],
    "path" -> path,
    "rows" -> report,
    "note" -> "Authority is vendor/fsot_compute.py; this package must track it."
  |>
];

End[];
EndPackage[];
