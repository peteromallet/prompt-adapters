# Data 10x plan — contingent strategy for using the 10× dataset

**Superseded by [NEXT_BEST_BET_PLAN.md](./NEXT_BEST_BET_PLAN.md)** as of 2026-04-25 — the v2 corpus sequence (dryrun → warmstart → warmstart_bigctx) replaced the original data_10x trajectory; new pre-registered plan and decision gates live there.

Status: drafted while experiment **006 (no-trunk projector)** is training and the
**10× dataset** (~10k train pairs vs 1k) is being fetched on the same pod. This
document specifies how the 10× data is used in the immediately-following
experiment (007), and what 007 looks like, *contingent on what 006 reports*.

This doc cites and does not duplicate:

- [`STRATEGY.md`](./STRATEGY.md) — claims, capability gates, decision principles.
- [`PROCESS.md`](./PROCESS.md) — experiment lifecycle (plan → launch → finalize → close).
- [`LEARNINGS.md`](./LEARNINGS.md) — cross-project findings (instruction quality, projector collapse, contrastive non-monotonicity).
- [`ROADMAP.md`](./ROADMAP.md) — current queue and gates.

Read the experiment learnings before acting:
[`004 (projector-contrastive)`](../experiments/2026-05-text-004-projector-contrastive/LEARNINGS.md),
[`005 (stronger-contrastive — refuted)`](../experiments/2026-05-text-005-stronger-contrastive/LEARNINGS.md),
[`006 (no-trunk — running)`](../experiments/2026-05-text-006-projector-no-trunk/experiment.yaml).

## TL;DR

- 006 is the last cheap architectural lever at the prefix-K/V primitive. Its
  outcome dictates whether 007 (10× data) is a *consolidation*, a *fix*, or a
  *coffin nail*.
- The 10× data alone is ~$1.50 LLM-instruct + ~$0.04 fetch and is already
  produced. The constraint is GPU time on the training run, not data.
- All three branches share one rule: do not run 007 without re-running pathway
  probes alongside the standard five-test battery. T2 in isolation has
  repeatedly misled this program (002, 005). Cite [`LEARNINGS.md` § Eval](./LEARNINGS.md).

## What "10× data" means concretely

| Register    | 1× train | 10× train (target) | Mechanism            |
|-------------|---------:|-------------------:|----------------------|
| poetry      |      566 |             ~4 000 | per-author cap 20 → 150 (41 authors × 122 docs avg) |
| screenplay  |      336 |             ~4 000 | per-movie cap 6 → 30 (198 movies in cache) |
| essay       |       54 |             ~1 000 | per-author cap 12 → 200; bounded by ~7 qualifying essayists |
| speech      |       15 |               ~500 | per-president cap 15 → 200; bounded by ~12 docs/president |
| **total**   |      971 |           **~9 500** | author-disjoint splits preserved (test enforced by `tests/test_register_splits.py`) |

Files: `data/pairs/{train,val,test}.llm.10x.jsonl` (separate from `*.llm.jsonl` so
existing experiments remain reproducible). Same schema, same 4 registers, same
3-layer leak firewall. LLM-instructed via Claude haiku, ~$1.30 cost.

## Branch A — 006 succeeds decisively

**Trigger** (all four 006 must-pass criteria, see [006 yaml](../experiments/2026-05-text-006-projector-no-trunk/experiment.yaml)):

- T3b LLM-judge style-match adapter_wins ≥ 12/20 (≥ 60%, decisive PASS not WEAK).
- T2 vs prompted_baseline ≥ 60% at n=20.
- LLM-judge α-blend signal ≥ 0.4, monotonic, endpoints frac_own α=0 < 0.30
  and α=1 > 0.85.
- Pathway cos_K_first for swap variant < 0.40.

If all four hit, **C1 is supported** ([`STRATEGY.md` § Claims under test](./STRATEGY.md#claims-under-test))
and **C3 has decisive directional evidence**.

### 007 in branch A: consolidation experiment (10× data, same recipe as 006)

- **Config**: `text-ip-adapter/configs/stage1_gemma_no_trunk_10x.yaml`
  — clone of `stage1_gemma_no_trunk.yaml`, only diffs:
  - `data.train_path: data/pairs/train.llm.10x.jsonl`
  - `data.val_path: data/pairs/val.llm.10x.jsonl`
  - `data.test_path: data/pairs/test.llm.10x.jsonl`
  - `training.max_steps: 6300` (sqrt(10) ≈ 3.16 × 2000 ≈ 6320; see § Schedule below)
  - `training.warmup: 600` (proportional)
  - `training.output_dir: checkpoints/stage1_gemma_no_trunk_10x`
- **Training schedule**: max_steps 6300 (sqrt-data scaling); cosine to ~0; eval
  at step 1000/3000/6300 to confirm the 006 phase-transition pattern still holds
  at scale.
- **Cost estimate**: ~117 min on RTX 4090 ≈ $1.35 train + $0.20 eval (capability
  + pathway probes) = **~$1.55**.
- **Must-pass criteria** (sharper than 006 because we're consolidating, not
  hoping):
  - T3b LLM-judge ≥ 65% (vs 006's ≥ 60% — confidence interval should tighten with
    more diverse train; n=20 still hard rule, see [`LEARNINGS.md` § Methodology](./LEARNINGS.md#methodology)).
  - T2 vs prompting ≥ 65%.
  - α-blend LLM-judge signal ≥ 0.5 (vs 006's ≥ 0.4) and endpoints α=0 < 0.25 /
    α=1 > 0.90.
  - Pathway cos_K_first for swap variant ≤ 0.35.
- **What 007 promotes / refutes**:
  - All four hit → C1 promoted from "supported" to "decisively supported";
    C3 promoted from "directional" to "supported"; the program ships its first
    "moat" capability and unblocks C2.
  - T3b ≥ 60% but α-signal flat → C1 holds, C3 demoted to "open"; cap C3 work
    until a follow-up architectural change targets the style-axis specifically.
  - T3b drops vs 006 → "more data hurts" is a strong negative; investigate data
    leak, instruction-quality regression, or per-register imbalance before any
    further training.
- **What comes after 007 in branch A**: 008 = **C2 cross-modality port** (audio,
  likely MusicGen with voice/timbre references). The exact shape of 008 is
  pre-empted; the recipe (frozen base, perceiver encoder, prefix injection,
  author-paired data, contrastive on K/V) ports as a unit. See
  [`ROADMAP.md` § Next project candidates](./ROADMAP.md#next-project-candidates-gated-on-c1).
  Long-context probe (C4) becomes a fast follow-up that fits in the same
  capability run.

## Branch B — 006 partial

**Trigger** (006 hits some but not all of its must-pass set):

- T3b ≥ 60% but α-signal stays weak (< 0.4); OR
- α-signal strong but T3b stalls at 50–55%; OR
- T2 holds and the pathway probe is mixed (e.g. cos_K_first swap improves but
  random/code regress).

The adapter conditions on references but weakly. The diagnosis is
"undertrained on undersized data," consistent with
[`LEARNINGS.md` § Data: 'Minimum viable data: ~1000 pairs gives signal of mechanism but not of style match.'](./LEARNINGS.md#data).

### 007 in branch B: data-scale lever on the 006 recipe

- **Config**: `text-ip-adapter/configs/stage1_gemma_no_trunk_10x.yaml` (same as
  branch A above; the recipe doesn't change, only the data does — that's the
  whole point of the lever).
- **Training schedule**: max_steps 8000 (slightly above sqrt-data because
  we *expect* under-training; warmup 800, cosine to ~0; eval at 1000/3000/5000/
  8000 to detect over-training).
- **Cost estimate**: ~150 min on RTX 4090 ≈ $1.75 train + $0.20 eval = **~$1.95**.
- **Must-pass criteria** (the bar the program needs to clear C1 decisively):
  - T3b ≥ 60% with LLM-judge adapter_wins ≥ 12/20. **This is the load-bearing
    threshold. Anything below 60% at n=20 is consistent with coin-flip and the
    program does not get to claim C1.**
  - T2 vs prompting ≥ 60% (no regression vs 006).
  - α-blend LLM-judge signal ≥ 0.4 with endpoints frac_own α=0 < 0.30 / α=1 > 0.85.
  - Pathway cos_K_first for swap < 0.40 AND for code < 0.50 (i.e. same-domain
    discrimination holds; this is where 005 regressed).
  - T4 mem/leak both 0%. Non-negotiable.
- **What 007 promotes / refutes**:
  - All four hit → branch B converges with branch A; C1 supported; move to
    capability scaling and C2 port.
  - T3b 55–59% (still weak) → the prefix-K/V primitive is a genuinely
    underpowered injection mechanism at 4B params. The recommended next move is
    **not** more data — it's a structurally different injection (Flamingo-style
    per-layer cross-attention, see [`STRATEGY.md` § Intellectual lineage](./STRATEGY.md#intellectual-lineage)).
  - T3b regresses below 50% at 10× → strong negative for the data-undertraining
    diagnosis; reconsider whether the projector ablation (006) was actually a
    generalizable architecture or a small-data overfit. Open new diagnostic
    experiment 008 mirroring 003's pathway probe on the 007 checkpoint.
- **What comes after 007 in branch B**: depends on outcome above. Best case →
  C2 audio port (same as branch A). Middle case → 008 = Flamingo cross-attention
  ablation on text (`text-gemma3-flamingo`, already on the roadmap). Worst case
  → 008 = pathway re-diagnosis to localize where 10× data failed to help.

## Branch C — 006 fails like 005

**Trigger** (006 hits zero or one of its must-pass set):

- T3b at 50–55% (coin flip / regressed); AND
- α-signal flat or inverted; AND
- pathway cos_K_first either stays high across the board (no projector unblock)
  or splits non-uniformly the way 005 did (outliers far apart, same-domain
  collapsed).

This is the "we hit the wall" outcome. The cheap-architecture space at the
prefix-K/V primitive is exhausted on five experiments (002 → 003 → 004 → 005 →
006). The minimum-bar gate from
[`STRATEGY.md` § "Beating prompting is necessary but not sufficient"](./STRATEGY.md#beating-prompting-is-necessary-but-not-sufficient)
is at risk.

### 007 in branch C: 10× data on the BEST checkpoint, as a final controlled test

The argument: if the architecture has been explored on multiple axes and each
one failed at 1k pairs, scaling data 10× is the last cheap variable that
*could* matter. It probably won't, but it removes the variable cleanly so the
program can either claim "data wasn't the problem" or recover.

- **Config**: `text-ip-adapter/configs/stage1_gemma_contrastive_10x.yaml`
  — clone of `stage1_gemma_contrastive.yaml` (the **004** config; this is the
  closest thing the project has to a working baseline because 004 is the only
  experiment that produced a directional positive on α-blending, see [004 LEARNINGS](../experiments/2026-05-text-004-projector-contrastive/LEARNINGS.md#headline)).
  Only diffs:
  - `data.{train,val,test}_path: data/pairs/{train,val,test}.llm.10x.jsonl`
  - `training.max_steps: 6300` (sqrt-data scaling on 004's 2000 step base;
    same heuristic as branches A/B)
  - `training.warmup: 600`
  - `training.output_dir: checkpoints/stage1_gemma_contrastive_10x`
- **Why 004's recipe and not 006's in branch C**: if 006 fails it failed
  *because* the no-trunk architecture didn't help at 1k pairs. Running it at
  10k bets on the same architecture working at scale — possible, but riskier
  than reverting to the only checkpoint that produced any positive directional
  evidence (α-blend 6/8 monotonic, cos_K/V dropped from 0.91 → 0.41). 007 in
  branch C is a controlled data-scale lever, not an architecture re-bet.
- **Training schedule**: max_steps 6300; warmup 600; cosine to ~0;
  eval at step 1000/3000/6300.
- **Cost estimate**: ~117 min on RTX 4090 ≈ $1.35 train + $0.20 eval = **~$1.55**.
- **Must-pass criteria** (sharply scoped — branch C is a falsifier):
  - T3b ≥ 60%. If this hits the program reverses out of strategic-rescope mode
    and rejoins branch B's trajectory.
  - T2 vs prompting ≥ 60%.
  - Pathway cos_K_first for swap < 0.40.
  - (α-blend tracked but not gating — branch C is about C1 first, C3 later.)
- **What 007 promotes / refutes**:
  - All hit → C1 supported via 004-recipe-at-scale; the no-trunk architecture
    (006) was a local minimum that happened not to scale; reconcile and
    update [`LEARNINGS.md`](./LEARNINGS.md). Consolidation continues.
  - All miss → **strategic rescope is required**. The prefix-K/V primitive at
    4B-param scale + 10k LLM-instructed pairs does not produce reference-driven
    style transfer beyond coin-flip. Three options, ordered by program cost:
    1. **Pivot to Flamingo per-layer cross-attention** (`text-gemma3-flamingo`,
       on roadmap). Different injection mechanism, same data infrastructure;
       tests whether prefix-K/V *specifically* is the bottleneck.
    2. **Scale model from 4B to 12B** (Gemma-3-12B with offload). Tests whether
       4B has insufficient attention bandwidth to ingest the prefix signal.
       Higher cost (~$5/run) but cheap relative to abandoning the program.
    3. **Rescope program claims**. Per
       [`STRATEGY.md` § What would cause us to pivot or abandon](./STRATEGY.md#what-would-cause-us-to-pivot-or-abandon),
       narrow C1 from "beats prompting on style transfer" to "context-efficient
       prompting with weak conditioning" and retire the moat-capability claim.
- **What comes after 007 in branch C**: see the three options above. Run them
  in order. Stop after any of them produces decisive C1 evidence.

## Cross-cutting design rules (apply in every branch)

1. **Re-run pathway probes alongside T2/T3b.** T2 has spuriously fired three
   times at this program scale (002, 005). The pathway probe (cos_K_first across
   own/swap/zero/random/code) localizes failure inside the encoder→projector→
   injection chain. See [`LEARNINGS.md` § Eval: 'Conditioning-pathway probes (cos_z / cos_K/V / gen_Jaccard ...) are the load-bearing diagnostic.'](./LEARNINGS.md#eval).
2. **n ≥ 20 probes for any T2/T3b verdict.** Hard rule.
   See [`PROCESS.md` § Hard rules](./PROCESS.md#hard-rules).
3. **Author-disjoint splits enforced at pair time.** `tests/test_register_splits.py`
   gates the 10× data the same way it gates the 1× data; no register split is
   shipped without that test passing. See [`LEARNINGS.md` § Data](./LEARNINGS.md#data).
4. **Pre-register the hypothesis.** Every 007 variant gets its hypothesis +
   must-pass criteria written into `experiments/<id>/experiment.yaml` and
   `README.md` *before* launch.
   See [`PROCESS.md` § Plan phase](./PROCESS.md#plan-phase).
5. **Sqrt-data scaling for max_steps.** This program's prior experiments used
   2000 steps at 971 pairs. At 10× pairs, sqrt(10) × 2000 ≈ 6300 is the default;
   branch B raises that to 8000 because branch B is specifically the
   "undertrained" hypothesis. Keep the cosine schedule shape — see
   [`projects/text-gemma3-prefix-kv/LEARNINGS.md`](../projects/text-gemma3-prefix-kv/LEARNINGS.md):
   *"Loss curve is SLOW throughout training (14.8% drop over 2000 steps). Cosine
   schedule pulls LR to ~0 by end, but model didn't plateau from convergence —
   it ran out of learning rate."* This is exactly the failure mode 10× data +
   longer schedule is designed to fix.
6. **Don't consume the data before the eval contract is signed.** All three
   branches have explicit must-pass thresholds. Read them before launch; don't
   adjust them post-hoc. See [`PROCESS.md` § Common anti-patterns](./PROCESS.md#common-anti-patterns).

## Decision matrix at a glance

| 006 outcome | Branch | 007 config | 007 max_steps | 007 must-pass T3b | 007 cost | If 007 passes | If 007 fails |
|-------------|--------|-----------|---------------|-------------------|----------|---------------|--------------|
| All 4 must-pass | A | `stage1_gemma_no_trunk_10x.yaml` | 6300 | ≥ 65% | ~$1.55 | C1 decisively supported → C2 audio port (008) | re-diagnose data |
| Mixed | B | `stage1_gemma_no_trunk_10x.yaml` | 8000 | ≥ 60% | ~$1.95 | C1 supported → C2 port | Flamingo (008) or rescope |
| Coin flip / regressed | C | `stage1_gemma_contrastive_10x.yaml` (revert to 004 recipe) | 6300 | ≥ 60% | ~$1.55 | C1 recovered via data | Strategic rescope: Flamingo, 12B, or narrow claims |

## Cost summary

- 10× data fetch + LLM regen (one-time): **~$1.30–1.50** (Claude haiku ×
  ~10 000 pairs at $0.13/1000 from prior experience, see [project
  LEARNINGS § Surprises / fragilities](../projects/text-gemma3-prefix-kv/LEARNINGS.md#surprises--fragilities)).
- 007 in any branch: **~$1.55–1.95** all-in (training + eval + pathway).
- **Total budget for the entire branch chain through 007**: under **$3.50**.
  Cheap relative to the strategic value of the next decision.

## Open assumptions documented

- The sqrt-data scaling rule (sqrt(N_pairs) for max_steps) is heuristic, not
  derived from this project's loss-curve fit. It's the program's working rule
  per [`projects/text-gemma3-prefix-kv/LEARNINGS.md`](../projects/text-gemma3-prefix-kv/LEARNINGS.md).
  If 007's loss curve plateaus before max_steps, drop max_steps in 008.
- The 10× data targets ~9.5k train pairs, not exactly 10k. The bottleneck is
  qualifying authors per register (essay 7, speech ~25, see counts table
  above). If essay or speech yield is materially short of target after the run,
  the strategic recommendation is *not* to add new registers — see
  [`STRATEGY.md` § Decision principles: "Cheapest intervention first"](./STRATEGY.md#decision-principles).
  Adding a new register costs more than the marginal pairs return.
- pg19 / reddit registers remain broken (HF deprecated `trust_remote_code`).
  This is logged in [`LEARNINGS.md` § Infrastructure / ops](./LEARNINGS.md#infrastructure--ops).
  Both could be revived via Parquet conversions; doing so is a separate project,
  not in scope here.
- Branch C's "revert to 004 recipe" is a deliberate design choice and might be
  contested. The argument is that 004 is the only checkpoint with directional
  C3 evidence (α-blend 6/8 monotonic, see [004 LEARNINGS](../experiments/2026-05-text-004-projector-contrastive/LEARNINGS.md));
  scaling the only checkpoint that *had* a positive signal beats scaling 006
  if 006 is the failure trigger. If post-hoc 006 reveals a redeeming subset of
  signal that's worth scaling, branch C's config can flip to the 006 recipe at
  launch time — but the recipe choice should be a **pre-launch decision** with
  documented rationale, not a post-hoc tune.

## What this doc does not cover

- Training-script changes — none required for any branch; only config files.
- Eval-script changes — none required; the existing five-test battery + pathway
  probe + capability probes work unchanged at 10× scale.
- C2 (audio) cross-modality port — covered by the future
  `audio-musicgen-prefix-kv` project on
  [`ROADMAP.md` § Next project candidates](./ROADMAP.md#next-project-candidates-gated-on-c1).
- C4 (long-context) capability test — fits inside the same capability probe run
  any branch produces; not gated on data scale.

---

Document is meant to be checked in alongside the 10× data and updated *once* —
when 006 closes and the branch is selected. After that, the relevant 007
experiment shell is created via `tools/plan-experiment.sh` per
[`PROCESS.md`](./PROCESS.md), and this doc becomes a historical artifact.
