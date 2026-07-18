(* ::Package:: *)
(*
  FSOTDomains.wl — 35-domain parameter table + raw_S evaluation.

  Mirrors vendor/fsot_compute.py DomainConfig table (§5).
  Requires FSOTScalar.wl already loaded.
*)

(* Load after FSOTScalar.wl — extends FSOT` context. *)
BeginPackage["FSOT`"];

FSOTDomainTable::usage = "Association name -> domain parameter Association.";
FSOTDomainNames::usage = "List of 35 core domain names.";
FSOTDomainRawS::usage = "raw_S for a domain name or parameter Association.";
FSOTDomainAtlas::usage = "Dataset of all domains with evaluated raw_S.";
FSOTDomainPlot::usage = "BarChart of domain raw_S values.";

Begin["`Private`"];

(* Domain table: {name, D_eff, hits, delta_psi, delta_theta, observed} *)
(* C interpretation constants follow fsot_compute seed formulas. *)
$phi = (1 + Sqrt[5])/2;
$gamma = N[EulerGamma, 30];
$e = E; $pi = Pi;
$alpha = Log[$pi]/($e*$phi^13);
$chaos = (-Log[2]/$phi)/(Sin[$pi/$e]*Sqrt[2]);
$aBleed = Sin[$pi/$e]*$phi/Sqrt[2];
$cFactor = Module[{psi, eta, poof, cEff, pNew},
  psi = 1 - Exp[-1]; eta = 1/($pi - 1);
  poof = Exp[(-Log[$pi]/$e)/(eta*Log[$phi])];
  cEff = (1 - poof*Sin[psi*eta])*(1 + 0.01*N[Catalan]/($pi*$phi));
  pNew = ($gamma/$e)*Sqrt[2];
  cEff*pNew
];
$cCosm = 1/($phi*10);

domainRows = {
  {"Particle_Physics", 5, 0, 1., 1., True, $gamma/$phi},
  {"Quantum_Mechanics", 6, 0, 1., 1., True, $gamma/$phi},
  {"Atomic_Physics", 7, 0, 0.85, 1., True, $e/$pi},
  {"Physical_Chemistry", 8, 0, 0.5, 1., True, $e/$pi},
  {"Chemistry", 8, 0, 0.6, 1., True, $e/$pi},
  {"Electromagnetism", 9, 0, 0.7, 1., True, $e/$pi},
  {"Molecular_Chemistry", 9, 0, 0.5, 1., True, Log[$pi]/$e},
  {"Optics", 10, 0, 0.6, 1., True, $pi/$e},
  {"Acoustics", 10, 0, 0.3, 1., True, $aBleed/Sqrt[2]},
  {"Quantum_Computing", 11, 0, 0.5, 1., False, Sqrt[2]/$e},
  {"Quantum_Optics", 11, 0, 0.6, 1., True, $pi/$e},
  {"Biology", 12, 0, 0.08, 1., False, Log[$phi]/Sqrt[2]},
  {"Thermodynamics", 15, 1, 0.9, 1., True, $gamma/$e},
  {"Biochemistry", 13, 1, 0.35, 1., True, Log[$phi]/Sqrt[2]},
  {"Neuroscience", 14, 1, 0.7, 1., True, $cFactor},
  {"Condensed_Matter", 14, 0, 0.5, 1., True, $aBleed/$e},
  {"Fluid_Dynamics", 15, 1, 0.9, 1., False, $aBleed/$phi},
  {"Nuclear_Physics", 15, 1, 1., 1., True, $alpha/$phi},
  {"Ecology", 15, 1, 0.2, 1., False, Log[$phi]/$phi},
  {"Meteorology", 16, 2, 0.8, 1., False, $chaos},
  {"Materials_Science", 10, 0, 0.5, 1., True, ($aBleed*(1+Cos[Sin[(1-Exp[-1])/(Pi-1)]]/$phi))/$e},
  {"Psychology", 16, 1, 1.15, 1., True, $gamma/$e},
  {"Atmospheric_Physics", 17, 2, 0.8, 1., False, $chaos},
  {"Oceanography", 17, 1, 0.7, 1., False, ($aBleed*(1+Cos[Sin[(1-Exp[-1])/(Pi-1)]]/$phi))/$phi},
  {"Seismology", 18, 2, 1.2, 1., False, $chaos/2},
  {"Sociology", 18, 3, 1.5, 1., True, $gamma/Log[$pi]},
  {"High_Energy_Physics", 7, 1, 0.95, 1., True, $alpha/Sqrt[2]},
  {"Geophysics", 19, 2, 1., 1., False, $chaos},
  {"Astronomy", 20, 1, 1., 1., True, $pi^2/$phi},
  {"Economics", 20, 3, 1.5, 1., True, $gamma/Log[$pi]},
  {"Planetary_Science", 21, 1, 0.9, 1., True, $pi^2/$phi},
  {"Quantum_Gravity", 22, 0, 1., 1., False, 1/$phi^2},
  {"Particle_Astrophysics", 24, 0, 0.8, 1., False, $pi^2/$e},
  {"Astrophysics", 24, 1, 1., 1., True, $pi^2/$phi},
  {"Cosmology", 25, 0, 1., 1., False, $cCosm}
};

FSOTDomainTable[] := Association @@ Table[
  row[[1]] -> <|
    "name" -> row[[1]],
    "D_eff" -> row[[2]],
    "hits" -> row[[3]],
    "delta_psi" -> row[[4]],
    "delta_theta" -> row[[5]],
    "observed" -> row[[6]],
    "C" -> row[[7]]
  |>,
  {row, domainRows}
];

FSOTDomainNames[] := Keys[FSOTDomainTable[]];

FSOTDomainRawS[name_String] := Module[{d},
  d = FSOTDomainTable[][name];
  If[MissingQ[d], Return[$Failed]];
  FSOTRawS[
    "D_eff" -> N[d["D_eff"]],
    "recent_hits" -> N[d["hits"]],
    "delta_psi" -> N[d["delta_psi"]],
    "delta_theta" -> N[d["delta_theta"]],
    "observed" -> d["observed"]
  ]
];

FSOTDomainRawS[d_Association] := FSOTRawS[
  "D_eff" -> N[d["D_eff"]],
  "recent_hits" -> N[Lookup[d, "hits", 0]],
  "delta_psi" -> N[d["delta_psi"]],
  "delta_theta" -> N[Lookup[d, "delta_theta", 1.]],
  "observed" -> Lookup[d, "observed", False]
];

FSOTDomainAtlas[] := Dataset @ Table[
  Module[{d = FSOTDomainTable[][name], s},
    s = FSOTDomainRawS[name];
    <|
      "domain" -> name,
      "D_eff" -> d["D_eff"],
      "delta_psi" -> d["delta_psi"],
      "observed" -> d["observed"],
      "raw_S" -> N[s, 12]
    |>
  ],
  {name, FSOTDomainNames[]}
];

FSOTDomainPlot[] := Module[{atlas, pairs},
  atlas = Normal @ FSOTDomainAtlas[];
  pairs = SortBy[{#domain, #raw_S} & /@ atlas, Last];
  BarChart[
    pairs[[All, 2]],
    ChartLabels -> Placed[pairs[[All, 1]], Axis],
    BarOrigin -> Left,
    ImageSize -> 700,
    PlotLabel -> "FSOT raw_S by core domain (seed-derived, zero free parameters)",
    AxesLabel -> {None, "raw_S"}
  ]
];

End[];
EndPackage[];
