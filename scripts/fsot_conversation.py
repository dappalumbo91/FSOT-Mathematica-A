#!/usr/bin/env python3
"""
FSOT multi-turn conversation — Python living dialogue surface.

Direction: full conversational capability → path to GPT-class fluency
on the domain-allocated FSOT LLM (occupation skeleton + fluent surface).

  turn  = observe user text → route domain → choose mode → generate → STM/LTM

Modes (intent-driven, keyword cues — seed-locked, not trained classifiers):
  brief   → 1 fluent structured sentence
  explain → claim bank first (substance); optional short organ seal
  deep    → deep claims (+ multi-topic) then optional organ seal
  turn    → explain if how/why; else paragraph tissue
  dream   → multi-domain fluent sweep
  meta    → identity / formula / authority + fluent seal
  recall  → LTM hit + fluent
  remember→ write LTM + ack sentence

Explanatory path (substance over empty coherence):
  claims  = data/explanatory_pack.json (prior literature continuity + FSOT spine)
  stance  = Newton not replaced by relativity; literature still teaches; FSOT unifies
  tissue  = occupation fluent seal only after claims

Fluency path:
  content   = claims first, then role occupation tissue
  surface   = Φ-indexed English templates + hybrid micro-fill
  discourse = claim roles + conversation framing / anaphora

Continuity:
  domain inertia when cues weak
  ban_pool from prior reply tokens (anti-clone across turns)
  active concepts from STM
  fluid-ish folds (hits, D_eff nudge) like living mind

  python scripts/fsot_conversation.py --smoke
  python scripts/fsot_conversation.py --chat
  python scripts/fsot_conversation.py --once "what is fsot?"
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(r"I:\fsot in mathmatica")
DATA = HOME / "data"
MEM = HOME / "memory"
MICRO = DATA / "microscope"
sys.path.insert(0, str(HOME / "scripts"))

import run_fsot_llm_python as eng  # noqa: E402
import fsot_explain as fexp  # noqa: E402

PHI = eng.PHI
LTM_PATH = MEM / "long_term_memory.json"
LIVING_MIND = MEM / "living_mind.json"
SKILL_PACKS = DATA / "skill_packs.json"
STM_SESSION = MEM / "conversation_session.json"
CONV_REPORT = DATA / "conversation_report.json"
CONV_MICRO = MICRO / "conversations.json"
EXPLAIN_PACK = DATA / "explanatory_pack.json"


def _phi_lead(tick: int, domain: str) -> str:
    """Question lead-ins — closed discourse surface."""
    leads = [
        f"Here is how I read that in the {domain} fold.",
        f"Let me walk the occupation path on {domain}.",
        "The short answer sits on the seeds; the arc fills the rest.",
        f"In {domain} terms, this is the path I see.",
        "Addressing that directly:",
    ]
    return leads[int((tick + 1) * PHI * 2) % len(leads)]

# ---- intent cues (occupation, not free classifier weights) ----
INTENT_CUES: list[tuple[str, tuple[str, ...]]] = [
    ("meta", ("who are you", "what are you", "identity", "your name", "introduce")),
    ("meta", ("formula", "equation", "scalar law", "what is s =", "raw_s", "seeds")),
    ("meta", ("authority", "lean", "proof", "verify", "verification", "archive")),
    ("remember", ("remember that", "remember this", "store that", "save this fact")),
    ("recall", ("recall", "what do you remember", "ltm", "long term", "prior memory")),
    ("dream", ("dream", "associate across", "cross domain", "sweep domains")),
    # explain = substance (claim bank); deep = fuller multi-claim
    ("deep", ("explain fully", "in depth", "full argument", "walk through", "prove that")),
    ("explain", (
        "explain", "why ", "why does", "why are", "why is", "how does", "how do",
        "how is", "how are", "what does", "what is the difference", "describe how",
        "tell me why", "tell me how", "how exactly", "what does fsot",
    )),
    ("brief", ("yes or no", "status", "ping", "hello", "hi ", "hey", "ok?", "short answer")),
    ("turn", ("tell me", "what is", "describe", "talk about")),
]


def _wants_substance(text: str) -> bool:
    """How/why/explain questions need claims, not empty occupation arcs."""
    t = text.lower().strip()
    if any(
        k in t
        for k in (
            "explain",
            "why ",
            "why?",
            "how does",
            "how do",
            "how is",
            "how are",
            "how exactly",
            "replace",
            "instead of",
            "does fsot",
            "what about newton",
            "what about relativ",
            "standard model",
            "prior literature",
            "continuity",
        )
    ):
        return True
    if t.startswith(("why", "how", "does ", "is fsot")):
        return True
    return False


def load_model() -> eng.FSOTLLM:
    vocab = None
    if eng.VOCAB.exists():
        vocab = json.loads(eng.VOCAB.read_text(encoding="utf-8"))["tokens"]
    model = eng.FSOTLLM(dim=32, vocab=vocab)
    for d in eng.DOMAIN_FOLDS:
        for tok in eng.SEED_CORE:
            model.allocate(tok, d, as_target=True)
    mp = eng.MODEL_OUT
    if mp.exists():
        doc = json.loads(mp.read_text(encoding="utf-8"))
        for k, v in (doc.get("embeddings") or {}).items():
            if "::" in k:
                dom, tok = k.split("::", 1)
                model.emb[(dom, tok)] = v
        for tok, doms in (doc.get("token_domain_allocation") or {}).items():
            for d in doms:
                model.allocate(tok, d, as_target=False)
        model.step = int(doc.get("step") or 0)
        model.recent_hits = float(doc.get("recent_hits") or 0.0)
    return model


def load_ltm() -> dict:
    if LTM_PATH.exists():
        try:
            return json.loads(LTM_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"entries": [], "updated": None}


def save_ltm(doc: dict) -> None:
    MEM.mkdir(parents=True, exist_ok=True)
    doc["updated"] = datetime.now(timezone.utc).isoformat()
    LTM_PATH.write_text(json.dumps(doc, indent=2), encoding="utf-8")


def classify_intent(text: str) -> str:
    t = text.lower().strip()
    for intent, cues in INTENT_CUES:
        if any(c in t for c in cues):
            return intent
    # questions default to turn (6-arc); long open statements deep if long
    if len(t.split()) >= 22:
        return "deep"
    if t.endswith("?") or any(t.startswith(w) for w in ("what", "how", "why", "where", "when", "who", "can", "does", "is ")):
        return "turn"
    return "turn"


def domain_with_inertia(text: str, prior_domain: str | None) -> str:
    """If cue mass is weak, keep prior domain (conversation continuity)."""
    t = text.lower()
    scores = {d: 0.0 for d in eng.DOMAIN_FOLDS}
    for dom, (w, keys) in eng.DOMAIN_CUES.items():
        hits = sum(1 for k in keys if k in t)
        if hits:
            scores[dom] += w * hits
    for cue, (dom, w) in eng.SOFT_CUES.items():
        if cue in t:
            scores[dom] += w
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] < 1.5 and prior_domain in eng.DOMAIN_FOLDS:
        return prior_domain
    if best[1] <= 0:
        return prior_domain if prior_domain in eng.DOMAIN_FOLDS else "linguistic"
    return best[0]


def extract_remember_payload(text: str) -> str:
    t = text.strip()
    for pref in (
        "remember that ",
        "remember this ",
        "store that ",
        "save this fact ",
        "remember: ",
    ):
        if t.lower().startswith(pref):
            return t[len(pref) :].strip()
    return t


def ltm_search(ltm: dict, query: str, limit: int = 4) -> list[dict]:
    toks = set(eng.tokenize(query))
    scored: list[tuple[float, dict]] = []
    for e in ltm.get("entries") or []:
        et = (e.get("text") or "") + " " + (e.get("tag") or "")
        etoks = set(eng.tokenize(et))
        if not etoks:
            continue
        overlap = len(toks & etoks) / max(len(toks), 1)
        if e.get("tag") and e["tag"] in query.lower():
            overlap += 0.5
        if overlap > 0:
            scored.append((overlap, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:limit]]


def load_skill_packs() -> dict:
    if SKILL_PACKS.exists():
        try:
            return json.loads(SKILL_PACKS.read_text(encoding="utf-8")).get("packs") or {}
        except json.JSONDecodeError:
            pass
    return {}


class FSOTConversation:
    """
    Multi-turn FSOT dialogue.
    One process pathway per turn; STM rolls; LTM disk-backed.
    Skill packs boost domain prefers mid-session; living_mind STM syncs both ways.
    """

    def __init__(self, model: eng.FSOTLLM | None = None, session_id: str = "default"):
        self.model = model or load_model()
        self.session_id = session_id
        self.tick = 0
        self.domain = "linguistic"
        self.stm: list[dict] = []
        self.ban_pool: set[str] = set()
        self.active_concepts: list[str] = []
        self.recent_hits = float(getattr(self.model, "recent_hits", 0.0) or 0.0)
        self.mood = "coherent"
        self.ltm = load_ltm()
        self.skill_packs = load_skill_packs()
        self._pull_living_stm()
        self._apply_skill_pack(self.domain)

    def _apply_skill_pack(self, domain: str) -> None:
        """Allocate pack tokens into domain organ (prefer occupation, not free weights)."""
        pack = self.skill_packs.get(domain) or {}
        for tok in pack.get("prefer_boost") or []:
            self.model.allocate(tok, domain, as_target=True)
        for phrase in pack.get("discourse") or []:
            for tok in eng.tokenize(phrase):
                if not eng.is_noise_token(tok):
                    self.model.allocate(tok, domain, as_target=True)

    def _pull_living_stm(self) -> None:
        """Import recent living_mind STM into conversation continuity."""
        if not LIVING_MIND.exists():
            return
        try:
            mind = json.loads(LIVING_MIND.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        living_stm = mind.get("stm") or []
        for e in living_stm[-6:]:
            if not isinstance(e, dict):
                continue
            # living mind entries use prompt/reply
            user = e.get("prompt") or e.get("user")
            reply = e.get("reply")
            if not user:
                continue
            # avoid duplicating if already in session stm
            if any(t.get("user") == user for t in self.stm):
                continue
            self.stm.append(
                {
                    "t": e.get("t"),
                    "tick": e.get("tick") or 0,
                    "user": user,
                    "intent": "living",
                    "mode": "living_sync",
                    "domain": e.get("domain") or mind.get("domain_focus") or "linguistic",
                    "reply": (reply or "")[:500],
                    "reply_tokens": eng.tokenize(reply or "")[:12],
                    "source": "living_mind",
                }
            )
        # concepts from living mind
        for c in mind.get("active_concepts") or []:
            if c not in self.active_concepts:
                self.active_concepts.append(c)
        self.active_concepts = self.active_concepts[:12]
        if mind.get("domain_focus"):
            # map Mathematica-style names lightly
            df = str(mind["domain_focus"]).lower()
            for k in eng.DOMAIN_FOLDS:
                if k in df or df in k:
                    self.domain = k
                    break

    def _push_living_stm(self, entry: dict) -> None:
        """Mirror last conversation turn into living_mind.json STM (best-effort)."""
        if not LIVING_MIND.exists():
            return
        try:
            mind = json.loads(LIVING_MIND.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        stm = list(mind.get("stm") or [])
        stm.append(
            {
                "t": entry.get("t"),
                "tick": entry.get("tick"),
                "prompt": entry.get("user"),
                "reply": entry.get("reply"),
                "domain": entry.get("domain"),
                "raw_S": entry.get("raw_S"),
                "trinary": entry.get("trinary"),
                "source": "fsot_conversation",
            }
        )
        if len(stm) > 32:
            stm = stm[-32:]
        mind["stm"] = stm
        mind["active_concepts"] = self.active_concepts
        mind["tick"] = max(int(mind.get("tick") or 0), int(entry.get("tick") or 0))
        mind["mood"] = self.mood
        # map domain focus label
        mind["domain_focus"] = entry.get("domain") or mind.get("domain_focus")
        try:
            LIVING_MIND.write_text(json.dumps(mind, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ---- fluid-ish state (mirrors living mind, seed-locked) ----
    def _nudge(self, text: str) -> None:
        toks = eng.tokenize(text)
        n = max(len(toks), 1)
        h = eng.token_unit(" ".join(toks)) if toks else 0.5
        self.recent_hits = min(self.recent_hits + 0.15 * min(n / 20.0, 1.0), 8.0)
        self.model.recent_hits = self.recent_hits
        folds = dict(eng.DOMAIN_FOLDS[self.domain])
        delta_psi = max(0.05, min(2.5, folds["delta_psi"] + 0.05 * (h - 0.5)))
        s = eng.raw_s(
            D_eff=folds["D_eff"],
            delta_psi=delta_psi,
            delta_theta=folds.get("delta_theta", 1.0),
            recent_hits=self.recent_hits,
            observed=True,
            N=folds.get("N", 1.0),
            P=folds.get("P", 1.0),
            rho=folds.get("rho", 1.0),
        )
        # trinary mood from collapse of raw_S (same family as GPU consensus)
        tri = eng.collapse(s) - 1  # collapse returns 0/1/2 → -1/0/+1-ish
        if tri > 0:
            tri = 1
        elif tri < 0:
            tri = -1
        else:
            tri = 0
        self.mood = {1: "expansive", -1: "contractive"}.get(tri, "coherent")
        self._last_S = s
        self._last_tri = tri
        seeds = [t for t in toks if t in eng.SEED_CORE or t in eng.UNIVERSAL]
        self.active_concepts = list(dict.fromkeys(seeds + toks[:8]))[:12]

    def _context_prefix(self) -> str:
        """Prior turn anchors for generation (not free-form chat history dump)."""
        parts: list[str] = []
        pack = self.skill_packs.get(self.domain) or {}
        boost = pack.get("prefer_boost") or []
        if boost:
            parts.append(" ".join(boost[:5]))
        if self.active_concepts:
            parts.append(" ".join(self.active_concepts[:6]))
        for turn in self.stm[-2:]:
            parts.append(turn.get("user", "")[:80])
            # last seal / tokens only
            toks = turn.get("reply_tokens") or []
            if toks:
                parts.append(" ".join(toks[:6]))
        return " ".join(parts).strip()

    def _enrich_prompt(self, user: str) -> str:
        pref = self._context_prefix()
        if pref:
            return f"{pref} | {user}"
        return user

    def _frame_open(self, user: str, intent: str) -> str:
        """Conversation framing — continuity / anaphora without free style models."""
        if self.tick == 0:
            return ""
        prior_dom = self.domain
        pack = self.skill_packs.get(prior_dom) or {}
        pack_lead = pack.get("lead") or f"On the {prior_dom} fold"
        concepts = [c for c in self.active_concepts if c not in ("the", "a", "and")][:3]
        topic = concepts[0] if concepts else prior_dom
        frames = [
            f"Staying with {topic}: ",
            f"{pack_lead}: ",
            f"On that same {prior_dom} fold: ",
            f"Building on what we just held: ",
            f"Carrying {topic} forward: ",
            "",
            "",
        ]
        # Φ-ish pick from tick
        return frames[int((self.tick + 1) * PHI) % len(frames)]

    def _cap(self, sent: str) -> str:
        if not sent:
            return ""
        s = sent.strip()
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        if s and s[-1] not in ".!?":
            s += "."
        return s

    def _meta_reply(self, user: str) -> dict:
        t = user.lower()
        if any(k in t for k in ("who are you", "what are you", "identity", "introduce")):
            body = (
                "I am the living FSOT conversational surface — a domain-allocated language "
                "process on seeds π, e, φ, γ, G with scalar S = K(T1+T2+T3). "
                "The Lean physical archive is authority; Mathematica is the formula microscope. "
                "Prior literature still teaches: Newton, relativity, the Standard Model — "
                "FSOT unifies deeper and does not erase the path that led here. "
                "Explanations should carry those claims, not empty occupation rhetoric."
            )
        elif any(k in t for k in ("formula", "equation", "scalar", "raw_s", "seed")):
            body = (
                "The scalar law is S = K (T1 + T2 + T3). Collapse sits at θ = C_eff · P_var. "
                "Learning uses η = |suction|·|poof|·|α|·|K|/(1+hits+|loss|) — no free Adam schedules, "
                "and consensus attention instead of softmax."
            )
        elif any(k in t for k in ("authority", "lean", "proof", "verify")):
            body = (
                "Verification lives on Lean + Coq + Isabelle + F* + Rust under "
                "I:/FSOT-Physical-Archive. I articulate, route, and remember; proofs kill claims there."
            )
        else:
            body = (
                "This conversation runs STM turns, LTM disk memory, and D_eff domain occupation, "
                "with fluent paragraph arcs and Therefore/Thus/Hence connectors when depth is required."
            )
        seal_prompt = self._enrich_prompt(user + " seed field truth")
        self.model.set_domain(self.domain)
        sealed = self.model.generate_structured(
            seal_prompt,
            n_slots=8,
            ban_tokens=set(self.ban_pool),
            fluent=True,
            phase="seal",
            phase_index=self.tick,
            use_bridges=False,  # meta seal: template only (fast, clean)
        )
        sent = self._cap(sealed.get("sentence") or sealed.get("generated") or "")
        reply = f"{body} {sent}".strip()
        return {
            "mode": "meta",
            "reply": reply,
            "structured": sealed,
            "paragraph": None,
            "domain": sealed.get("domain") or self.domain,
            "D_eff": sealed.get("D_eff"),
            "reply_tokens": list(sealed.get("tokens") or []),
            "arc": None,
            "connectors": [],
        }

    def _brief_reply(self, user: str) -> dict:
        g = self.model.generate_structured(
            self._enrich_prompt(user),
            n_slots=8,
            ban_tokens=set(self.ban_pool),
            fluent=True,
            phase="structure",
            phase_index=self.tick,
            use_bridges=False,  # brief: template fluent only
        )
        frame = self._frame_open(user, "brief")
        sent = self._cap(g.get("sentence") or g.get("generated") or "")
        return {
            "mode": "brief",
            "reply": (frame + sent).strip(),
            "structured": g,
            "paragraph": None,
            "domain": g.get("domain"),
            "D_eff": g.get("D_eff"),
            "reply_tokens": list(g.get("tokens") or []),
            "arc": None,
            "connectors": [],
        }

    def _paragraph_reply(
        self,
        user: str,
        n_sentences: int,
        *,
        stream: bool = False,
        stream_prefix: str = "",
    ) -> dict:
        # Seed paragraph bans with conversation ban_pool; keep fluent kwargs
        orig_gen_struct = self.model.generate_structured
        ban = set(self.ban_pool)

        def gen_with_ban(prompt, n_slots=None, ban_tokens=None, **kwargs):
            merged = set(ban) | set(ban_tokens or [])
            kwargs.setdefault("fluent", True)
            kwargs.setdefault("use_bridges", True)  # turn/deep: sparse free bridges
            return orig_gen_struct(prompt, n_slots=n_slots, ban_tokens=merged, **kwargs)

        frame = self._frame_open(user, "deep" if n_sentences >= 8 else "turn")
        u = user.lower().strip()
        lead = ""
        if u.endswith("?") and n_sentences >= 6:
            lead = _phi_lead(self.tick, self.domain) + " "
        prefix = (stream_prefix or "") + frame + lead
        if stream and prefix.strip():
            print(prefix, end="", flush=True)
            first_stream = True
        else:
            first_stream = False

        def on_step(step: dict) -> None:
            nonlocal first_stream
            if not stream:
                return
            sent = step.get("sentence") or ""
            if not sent:
                return
            kind = step.get("kind", "sentence")
            mark = "→" if kind == "connector" else "·"
            if first_stream:
                print(f"\n  {mark} {sent}", flush=True)
                first_stream = False
            else:
                print(f"  {mark} {sent}", flush=True)

        self.model.generate_structured = gen_with_ban  # type: ignore
        try:
            p = self.model.generate_paragraph(
                self._enrich_prompt(user),
                n_sentences=n_sentences,
                n_slots=8,
                fluent=True,
                on_step=on_step if stream else None,
            )
        finally:
            self.model.generate_structured = orig_gen_struct  # type: ignore

        connectors = [
            s["sentence"]
            for s in (p.get("steps") or [])
            if s.get("kind") == "connector"
        ]
        tokens: list[str] = []
        for s in p.get("steps") or []:
            tokens.extend(s.get("tokens") or [])
        body = p.get("paragraph") or ""
        reply = (frame + lead + body).strip()
        if stream:
            print(flush=True)
        return {
            "mode": "deep" if n_sentences >= 8 else "turn",
            "reply": reply,
            "structured": None,
            "paragraph": p,
            "domain": p.get("domain"),
            "D_eff": p.get("D_eff"),
            "reply_tokens": tokens,
            "arc": p.get("arc"),
            "connectors": connectors,
            "n_sentences": p.get("n_sentences"),
            "streamed": stream,
        }

    def _dream_reply(self, user: str) -> dict:
        domains = [
            "linguistic",
            "quantum",
            "cosmological",
            "neural",
            "medical",
            "consciousness",
        ]
        lines = [
            "Here is a cross-domain sweep — each organ speaks in its own D_eff, then we close the joint:"
        ]
        tokens: list[str] = []
        steps = []
        ban = set(self.ban_pool)
        for i, d in enumerate(domains):
            self.model.set_domain(d)
            cue = f"{user} {d} field structure seed"
            g = self.model.generate_structured(
                cue,
                n_slots=6,
                ban_tokens=ban,
                fluent=True,
                phase="interaction",
                phase_index=i,
                domain_override=d,
            )
            sent = self._cap(g.get("sentence") or g.get("generated") or "")
            lines.append(f"In {d}, {sent[0].lower() + sent[1:] if sent else ''}".rstrip("."))
            if lines[-1] and not lines[-1].endswith("."):
                lines[-1] += "."
            ban.update(g.get("tokens") or [])
            tokens.extend(g.get("tokens") or [])
            steps.append({"domain": d, "sentence": sent, "tokens": g.get("tokens")})
        anchors = [t for t in eng.tokenize(user) if t in eng.SEED_CORE] or ["seed", "field", "truth"]
        a, b, c = anchors[0], anchors[min(1, len(anchors) - 1)], "consensus"
        close = eng.assemble_fluent_connector("consequence", a, b, c, index=self.tick)
        lines.append(close)
        return {
            "mode": "dream",
            "reply": " ".join(lines),
            "structured": None,
            "paragraph": None,
            "dream_steps": steps,
            "domain": self.domain,
            "D_eff": eng.DOMAIN_FOLDS[self.domain]["D_eff"],
            "reply_tokens": tokens,
            "arc": ["dream_sweep", "consequence"],
            "connectors": [close],
        }

    def _recall_reply(self, user: str) -> dict:
        hits = ltm_search(self.ltm, user, limit=4)
        if not hits:
            preface = "I do not have a strong long-term match yet — the field is open."
        else:
            bits = [f"«{h.get('text')}»" for h in hits]
            preface = "From long-term memory I hold: " + " · ".join(bits) + "."
        g = self.model.generate_structured(
            self._enrich_prompt(user + " memory seed truth"),
            n_slots=8,
            ban_tokens=set(self.ban_pool),
            fluent=True,
            phase="measure",
            phase_index=self.tick,
            use_bridges=False,
        )
        sent = self._cap(g.get("sentence") or g.get("generated") or "")
        return {
            "mode": "recall",
            "reply": f"{preface} {sent}".strip(),
            "structured": g,
            "paragraph": None,
            "ltm_hits": hits,
            "domain": g.get("domain"),
            "D_eff": g.get("D_eff"),
            "reply_tokens": list(g.get("tokens") or []),
            "arc": None,
            "connectors": [],
        }

    def _explain_reply(self, user: str, *, depth: str = "turn") -> dict:
        """
        Substance first: retrieve FSOT + continuity claims, then a short organ seal.
        Fixes coherent-but-empty rhetoric.
        """
        doc = fexp.compose_explanation(
            user,
            depth=depth,
            pack=fexp.load_pack(EXPLAIN_PACK),
            max_topics=2 if depth == "deep" else 1,
        )
        # Prefer claim-bank domain when it is a real organ
        dom = doc.get("domain") or self.domain
        if dom in eng.DOMAIN_FOLDS:
            self.domain = dom
            self.model.set_domain(dom)
            self._apply_skill_pack(dom)

        body = doc.get("reply") or ""
        # Continuity reminder when free-params / TOE talk might sound like erasure
        t = user.lower()
        if any(k in t for k in ("replace", "wrong", "everything", "only fsot", "ignore")):
            stance = (
                " Continuity: prior literature still explains its regimes "
                "(Newton, relativity, Standard Model); FSOT unifies deeper — "
                "it does not delete the path that led here."
            )
            if "continuity" not in body.lower() and "newton" not in body.lower():
                body = body + stance

        # Optional short seal — tissue after substance, not instead of it
        seal = self.model.generate_structured(
            self._enrich_prompt(user + " seed truth seal"),
            n_slots=6,
            ban_tokens=set(self.ban_pool),
            fluent=True,
            phase="seal",
            phase_index=self.tick,
            use_bridges=False,
            domain_override=self.domain if self.domain in eng.DOMAIN_FOLDS else None,
        )
        seal_sent = self._cap(seal.get("sentence") or "")
        if seal_sent:
            body = f"{body} {seal_sent}"

        tokens = list(seal.get("tokens") or [])
        return {
            "mode": doc.get("mode") or f"explain_{depth}",
            "reply": body.strip(),
            "structured": seal,
            "paragraph": None,
            "explanation": doc,
            "domain": self.domain,
            "D_eff": eng.DOMAIN_FOLDS.get(self.domain, {}).get("D_eff"),
            "reply_tokens": tokens,
            "arc": [s.get("role") for s in doc.get("sections") or [] if s.get("kind") == "claim"],
            "connectors": [
                s["text"] for s in doc.get("sections") or [] if s.get("kind") == "glue"
            ],
            "n_claims": doc.get("n_claims"),
            "topics": doc.get("topics"),
        }

    def _remember_reply(self, user: str) -> dict:
        payload = extract_remember_payload(user)
        entry = {
            "t": datetime.now(timezone.utc).isoformat(),
            "tag": "dialogue",
            "text": payload,
            "domain": self.domain,
            "raw_S": getattr(self, "_last_S", None),
            "tick": self.tick + 1,
        }
        self.ltm.setdefault("entries", []).append(entry)
        save_ltm(self.ltm)
        g = self.model.generate_structured(
            f"remember seed truth {payload[:60]}",
            n_slots=8,
            ban_tokens=set(self.ban_pool),
            fluent=True,
            phase="seal",
            phase_index=self.tick,
            use_bridges=False,
        )
        sent = self._cap(g.get("sentence") or g.get("generated") or "")
        return {
            "mode": "remember",
            "reply": f"I have stored that in long-term memory: {payload}. {sent}",
            "structured": g,
            "paragraph": None,
            "ltm_entry": entry,
            "domain": g.get("domain") or self.domain,
            "D_eff": g.get("D_eff"),
            "reply_tokens": list(g.get("tokens") or []),
            "arc": None,
            "connectors": [],
        }

    def respond(
        self,
        user_text: str,
        force_mode: str | None = None,
        *,
        stream: bool = False,
    ) -> dict:
        user = (user_text or "").strip()
        if not user:
            return {"ok": False, "reply": "(empty)", "tick": self.tick}

        intent = force_mode or classify_intent(user)
        # Promote how/why/replace/continuity questions to claim-based explain
        if intent in ("turn", "deep") and _wants_substance(user):
            intent = "deep_explain" if intent == "deep" or "fully" in user.lower() else "explain"
        if intent == "explain" and ("fully" in user.lower() or "in depth" in user.lower()):
            intent = "deep_explain"

        self.domain = domain_with_inertia(user, self.domain)
        self.model.set_domain(self.domain)
        self._apply_skill_pack(self.domain)
        self._nudge(user)

        if intent == "meta":
            out = self._meta_reply(user)
        elif intent == "brief":
            out = self._brief_reply(user)
        elif intent == "explain":
            out = self._explain_reply(user, depth="turn")
            if stream:
                print(out.get("reply") or "", flush=True)
                out["streamed"] = True
        elif intent == "deep_explain":
            out = self._explain_reply(user, depth="deep")
            if stream:
                exp = out.get("explanation") or {}
                for sec in exp.get("sections") or []:
                    if sec.get("kind") in ("lead", "claim", "glue", "heading"):
                        mark = "→" if sec.get("kind") == "glue" else "·"
                        print(f"  {mark} {sec.get('text')}", flush=True)
                print(flush=True)
                out["streamed"] = True
        elif intent == "deep":
            out = self._paragraph_reply(user, n_sentences=8, stream=stream)
        elif intent == "dream":
            out = self._dream_reply(user)
        elif intent == "recall":
            out = self._recall_reply(user)
        elif intent == "remember":
            out = self._remember_reply(user)
        else:
            out = self._paragraph_reply(user, n_sentences=6, stream=stream)

        self.tick += 1
        # update ban pool (keep last ~24 occupation tokens)
        for t in out.get("reply_tokens") or []:
            if t and t not in eng.SEED_CORE:
                self.ban_pool.add(t)
        if len(self.ban_pool) > 48:
            # keep most recent-ish by rebuilding from STM
            self.ban_pool = set()
            for turn in self.stm[-4:]:
                for t in turn.get("reply_tokens") or []:
                    if t not in eng.SEED_CORE:
                        self.ban_pool.add(t)
            for t in out.get("reply_tokens") or []:
                if t not in eng.SEED_CORE:
                    self.ban_pool.add(t)

        entry = {
            "t": datetime.now(timezone.utc).isoformat(),
            "tick": self.tick,
            "user": user,
            "intent": intent,
            "mode": out.get("mode"),
            "domain": out.get("domain") or self.domain,
            "D_eff": out.get("D_eff"),
            "mood": self.mood,
            "skill_pack": self.domain if self.domain in self.skill_packs else None,
            "raw_S": getattr(self, "_last_S", None),
            "trinary": getattr(self, "_last_tri", None),
            "reply": out.get("reply"),
            "reply_tokens": out.get("reply_tokens") or [],
            "arc": out.get("arc"),
            "connectors": out.get("connectors") or [],
            "n_sentences": out.get("n_sentences"),
            "active_concepts": list(self.active_concepts),
        }
        self.stm.append(entry)
        if len(self.stm) > 48:
            self.stm = self.stm[-48:]
        # best-effort mirror into Mathematica living mind STM
        try:
            self._push_living_stm(entry)
        except Exception:
            pass

        return {
            "ok": True,
            "tick": self.tick,
            "intent": intent,
            "mode": out.get("mode"),
            "domain": entry["domain"],
            "D_eff": entry["D_eff"],
            "mood": self.mood,
            "reply": out.get("reply"),
            "connectors": out.get("connectors") or [],
            "arc": out.get("arc"),
            "n_sentences": out.get("n_sentences"),
            "n_claims": out.get("n_claims"),
            "topics": out.get("topics"),
            "entry": entry,
            "detail": {
                k: out[k]
                for k in (
                    "paragraph",
                    "structured",
                    "dream_steps",
                    "ltm_hits",
                    "ltm_entry",
                    "explanation",
                )
                if out.get(k) is not None
            },
        }

    def save_session(self, path: Path | None = None) -> Path:
        path = path or STM_SESSION
        MEM.mkdir(parents=True, exist_ok=True)
        doc = {
            "session_id": self.session_id,
            "saved_utc": datetime.now(timezone.utc).isoformat(),
            "tick": self.tick,
            "domain": self.domain,
            "mood": self.mood,
            "recent_hits": self.recent_hits,
            "active_concepts": self.active_concepts,
            "ban_pool": sorted(self.ban_pool)[:64],
            "stm": self.stm,
        }
        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        return path

    def load_session(self, path: Path | None = None) -> bool:
        path = path or STM_SESSION
        if not path.exists():
            return False
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.session_id = doc.get("session_id") or self.session_id
        self.tick = int(doc.get("tick") or 0)
        self.domain = doc.get("domain") or self.domain
        self.mood = doc.get("mood") or self.mood
        self.recent_hits = float(doc.get("recent_hits") or 0.0)
        self.active_concepts = list(doc.get("active_concepts") or [])
        self.ban_pool = set(doc.get("ban_pool") or [])
        self.stm = list(doc.get("stm") or [])
        return True


def export_conversation(conv: FSOTConversation, turns: list[dict] | None = None) -> Path:
    MICRO.mkdir(parents=True, exist_ok=True)
    turns = turns or [
        {
            "tick": e["tick"],
            "user": e["user"],
            "intent": e.get("intent"),
            "mode": e.get("mode"),
            "domain": e.get("domain"),
            "D_eff": e.get("D_eff"),
            "reply": e.get("reply"),
            "arc": e.get("arc"),
            "connectors": e.get("connectors"),
            "mood": e.get("mood"),
        }
        for e in conv.stm
    ]
    doc = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": conv.session_id,
        "n_turns": len(turns),
        "domain": conv.domain,
        "mood": conv.mood,
        "active_concepts": conv.active_concepts,
        "turns": turns,
        "formula": (
            "conversation_turn = intent_route(user) → "
            "{brief:fluent_structured | turn:paragraph_v3_fluent(6) | deep:paragraph_v3_fluent(8) | "
            "dream:domain_sweep | meta|recall|remember}; "
            "surface = Φ-template(role_map) + hybrid micro-fill; "
            "STM ban_pool + domain inertia + framing; LTM disk"
        ),
    }
    CONV_MICRO.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    # also attach to microscope score boards if present
    boards = MICRO / "score_boards.json"
    if boards.exists():
        micro = json.loads(boards.read_text(encoding="utf-8"))
        micro["conversation"] = doc
        forms = dict(micro.get("formulas") or {})
        forms["conversation"] = doc["formula"]
        micro["formulas"] = forms
        boards.write_text(json.dumps(micro, indent=2), encoding="utf-8")
    return CONV_MICRO


def smoke() -> int:
    print("=== FSOT CONVERSATION SMOKE ===")
    conv = FSOTConversation(session_id="smoke")
    script = [
        ("hello", None),
        ("who are you?", None),
        ("what is the scalar formula?", None),
        ("explain how language routes through domain occupation", None),
        ("explain fully why free parameters are the wrong architecture for FSOT", None),
        ("Does FSOT replace relativity and the Standard Model?", None),
        ("remember that PFLT aims at full universal communication", None),
        ("what do you recall about PFLT?", None),
        ("dream across domains about fluid meaning", None),
        ("how does quantum collapse connect to measure?", None),
        ("explain how medical signal diagnose works in the clinical field", None),
    ]
    report_turns = []
    for user, force in script:
        print(f"\n── USER ──\n{user}")
        r = conv.respond(user, force_mode=force)
        print(
            f"── FSOT [{r['mode']}|{r['domain']}|D_eff={r['D_eff']}|mood={r['mood']}|intent={r['intent']}] ──"
        )
        print(r["reply"])
        if r.get("connectors"):
            print("  connectors:", " | ".join(r["connectors"]))
        if r.get("arc"):
            print("  arc:", " → ".join(r["arc"]) if isinstance(r["arc"], list) else r["arc"])
        report_turns.append(r["entry"])

    path = export_conversation(conv)
    conv.save_session()
    report = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "n_turns": len(report_turns),
        "modes": [t.get("mode") for t in report_turns],
        "domains": [t.get("domain") for t in report_turns],
        "turns": report_turns,
        "conversation_export": str(path),
        "session": str(STM_SESSION),
    }
    CONV_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {CONV_REPORT}")
    print(f"Microscope conversation: {path}")
    print(f"Session STM: {STM_SESSION}")
    print("=== SMOKE COMPLETE ===")
    return 0


def chat_loop(*, stream: bool = True) -> int:
    print(
        "FSOT conversation (quit/exit to leave; /deep /brief /dream /recall /stream on|off /domain X)"
    )
    print("Deep/turn arcs stream sentence-by-sentence when streaming is on.")
    conv = FSOTConversation(session_id="live")
    conv.load_session()  # resume if any
    do_stream = stream
    while True:
        try:
            user = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user.lower() in ("quit", "exit", ":q"):
            break
        if user.lower().startswith("/stream"):
            arg = user[7:].strip().lower()
            if arg in ("off", "0", "false", "no"):
                do_stream = False
            elif arg in ("on", "1", "true", "yes", ""):
                do_stream = True
            print(f"  streaming={'on' if do_stream else 'off'}")
            continue
        if user.lower().startswith("/domain "):
            d = user[8:].strip().lower()
            if d in eng.DOMAIN_FOLDS:
                conv.domain = d
                conv._apply_skill_pack(d)
                print(f"  domain forced → {d} D_eff={eng.DOMAIN_FOLDS[d]['D_eff']}")
            else:
                print(f"  unknown domain; try: {', '.join(sorted(eng.DOMAIN_FOLDS))}")
            continue
        force = None
        if user.startswith("/deep "):
            force, user = "deep", user[6:]
        elif user.startswith("/brief "):
            force, user = "brief", user[7:]
        elif user.startswith("/dream"):
            force, user = "dream", user[6:].strip() or "cross domain associate"
        elif user.startswith("/recall"):
            force, user = "recall", user[7:].strip() or "memory seed"
        # stream turn/deep; other modes print whole reply after
        will_stream = do_stream and (force in (None, "deep", "turn") or (
            force is None and classify_intent(user) in ("turn", "deep")
        ))
        if will_stream:
            print(f"\nFSOT[{force or 'turn'}|{conv.domain}|streaming]>", flush=True)
        r = conv.respond(user, force_mode=force, stream=will_stream)
        if will_stream and r.get("streamed"):
            print(
                f"  [{r['mode']}|{r['domain']}|tick={r['tick']}|D_eff={r['D_eff']}]",
                flush=True,
            )
        else:
            print(f"\nFSOT[{r['mode']}|{r['domain']}|tick={r['tick']}]>\n{r['reply']}")
    conv.save_session()
    export_conversation(conv)
    print("Session saved.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="FSOT multi-turn conversation")
    ap.add_argument("--smoke", action="store_true", help="Batch multi-turn smoke demo")
    ap.add_argument("--chat", action="store_true", help="Interactive chat loop")
    ap.add_argument("--once", type=str, default="", help="Single turn then exit")
    ap.add_argument("--deep", action="store_true", help="Force deep (8-step) mode for --once")
    args = ap.parse_args()

    if args.smoke:
        return smoke()
    if args.chat:
        return chat_loop(stream=True)
    if args.once:
        conv = FSOTConversation(session_id="once")
        r = conv.respond(args.once, force_mode="deep" if args.deep else None)
        print(r["reply"])
        print(
            f"\n[{r['mode']}|{r['domain']}|D_eff={r['D_eff']}|intent={r['intent']}]",
            file=sys.stderr,
        )
        return 0

    # default: smoke when no flags (makes progress visible)
    return smoke()


if __name__ == "__main__":
    raise SystemExit(main())
