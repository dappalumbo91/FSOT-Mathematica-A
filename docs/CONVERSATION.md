# FSOT Conversation — full dialogue capability

## Direction

Turn the domain-allocated FSOT LLM into a **multi-turn conversational capability**:

- not a free-parameter chatbot  
- same seeds, scalar, D_eff occupation, PFLT prefers  
- STM + LTM memory hierarchy (living-mind lesson)  
- generation modes chosen by **intent cues** (not trained classifiers)

## Formula

```
conversation_turn =
  observe(user)
  → domain_with_inertia(prior_domain)
  → intent_route(user)
  → generate(mode)
  → STM append + ban_pool update
  → optional LTM write/read
```

| Mode | When | Generator |
|------|------|-----------|
| `brief` | hello / status / short | structured 8-role sentence |
| `turn` | default questions / explain | **paragraph_v2 n=6** (Therefore) |
| `deep` | “explain fully”, long argument | **paragraph_v2 n=8** (Therefore + Thus + Hence) |
| `dream` | dream / cross-domain | multi-domain structured sweep + Therefore close |
| `meta` | identity / formula / authority | fixed spine text + structured seal |
| `recall` | recall / LTM | long_term_memory search + structured |
| `remember` | “remember that …” | write LTM + ack |

### Why 8-step arcs matter here

In isolation, 6 is denser for publication.  
In **conversation**, `deep` turns need a full logical close:

```
emergence → structure → interaction → Therefore → measure → Thus → Hence → seal
```

That is the path toward proof-shaped universal communication (PFLT), not just pretty paragraphs.

## Continuity (what makes it *conversation*)

| Mechanism | Role |
|-----------|------|
| **Domain inertia** | Weak cues keep prior domain (topic stickiness) |
| **ban_pool** | Prior reply tokens demoted next turn (anti-clone) |
| **context prefix** | Active concepts + last seals enrich prompt anchors |
| **STM** | Rolling turns in `memory/conversation_session.json` |
| **LTM** | Durable facts in `memory/long_term_memory.json` |
| **hits / mood** | raw_S + collapse trinary after each observation |

## Run

```powershell
cd "I:\fsot in mathmatica"
python scripts/fsot_conversation.py --smoke   # multi-turn demo + export
python scripts/fsot_conversation.py --chat    # interactive
python scripts/fsot_conversation.py --once "what is fsot?"
python scripts/fsot_conversation.py --once "explain fully ..." --deep
```

Chat prefixes: `/deep `, `/brief `, `/dream`, `/recall`

## Mathematica microscope

```wolfram
Get["I:/fsot in mathmatica/FSOT/init.wl"]
FSOTMicroscopeLoad[]
FSOTMicroscopeConversation[]
FSOTMicroscopeConversation[1]
```

Exports:

- `data/microscope/conversations.json`
- `data/microscope/score_boards.json` → key `conversation`
- `data/conversation_report.json`
- `memory/conversation_session.json`

## Relation to Mathematica living mind

| Surface | Role |
|---------|------|
| `FSOTThink` / `Live_Dialogue.wls` | Fluid observer articulate (exact math twin) |
| `fsot_conversation.py` | **Primary dialogue** with structured + paragraph organs |
| Lean archive | Authority — claims still die there |

## Fluency path (toward GPT-class surface)

| Layer | Status |
|-------|--------|
| Role occupation skeleton | Done — same hybrid scorer |
| Φ English templates (`assemble_fluent`) | Done — phase-tinted sentences |
| Varied connectors (Therefore family) | Done |
| **Free bridges 4–12 tokens × 3** | Done — `generate_bridge` / `assemble_skeleton_bridges` |
| Fluency discourse curriculum | Done — `expand_fluency_curriculum.py` |
| Domain skill packs | Done — `data/skill_packs.json` |
| Living mind STM sync | Done — pull/push `memory/living_mind.json` |
| Conversation framing / anaphora | Done |
| Classic slot glue kept | `sentence_classic` for microscope |

**Ontology:** fluency is *realization*, not free ranking. Content tokens still come from domain occupation; bridges are scored free-gen with diet/ban.

Modes write `structured_slots_v4_bridges` / `paragraph_v3_fluent`.

### Expand fluency pairs + full retrain

```powershell
python scripts/expand_fluency_curriculum.py
python scripts/run_fsot_llm_python.py          # full retrain (fluency + medical elevated)
# or light warm only:
python scripts/expand_fluency_curriculum.py --quick-train
```

Train mix now includes `fluency_discourse` (~14% of epoch) and medical oversample in fine-tune.

## Chat streaming

```powershell
python scripts/fsot_conversation.py --chat
```

- Turn/deep arcs print **sentence-by-sentence** as each organ step completes  
- `/stream on|off` toggles streaming  
- `/domain medical` forces organ + skill pack  
- `/deep …` full 8-step arc with live connectors  

## Growth path (next after this)

1. Multilingual PFLT surface packs (same skeleton, other languages)  
2. Optional audio/spectrum observe folds (video_llm lesson)  
3. Token-level stream inside free bridges (finer than sentence stream)  
4. Full retrain after each major fluency curriculum bump  
