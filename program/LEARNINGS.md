# Program Learnings

Cross-project findings that apply beyond any single experiment or project. Updated as patterns surface. Project-specific learnings live in each project's own LEARNINGS.md.

## Methodology

- **The five-test eval battery is the right unit for style work.** T1 discrimination, T2 vs prompted baseline, T3 style carryover, T4 memorization/leak, T5 loss curve. Each one probes a distinct failure mode. First experiment (text-001) validated the battery — each test produced interpretable signal and the combined pattern correctly diagnosed the weakness.
- **Pre-register the hypothesis.** Every experiment's README should contain its hypothesis *before* the run starts. Experiment 001 was set up this way via megaplan-mode planning; experiment 002's README was seeded with its hypothesis when training launched. This prevents retrofitting interpretation to outcomes.
- **LLM-judge is cheap enough to be a first-class signal.** `claude-haiku-4-5` at ~$0.001/judgment, subsecond latency. Even at n=20 per probe it's under $0.10 per evaluation. Worth using from day one as the primary quality signal for T2.
- **Probe-at-training-step design.** Sample 4 variants (adapter / adapter_swap / no_ref / prompted_baseline) at fixed training steps, write to `samples.jsonl`. This gave us a continuous picture of adapter evolution, and made the "discrimination kicks in at step 600-1100" phase transition visible. Keep this pattern across all modalities.
- **Surface-feature metrics are noisy at small-n.** Em-dash rates, archaic word rates, TTR — these have too much per-probe variance to yield clean signal on n=4 probes. Either scale probes to n≥30 or lean harder on LLM-judge.
- **Run eval at n≥20 before writing up — this is a hard rule.** Smaller probe sets are smoke tests, not final evidence.

## Instructions / test-rig quality

- **Instruction quality is a first-order variable.** Experiment 001 used rule-based instructions like `"Compose a brief piece on the theme of how and solemn"` — pure noise. The model had to use the prefix channel to compensate, which polluted the style signal and almost certainly explains T3's FAIL. **Any architectural experiment is uninterpretable if the instruction channel is noisy.** Fix test-rig before testing architecture.
- **Rule-based theme extraction doesn't work.** Top-frequency-non-stopword extraction pulls in stopwords, header tokens (`act`, `iii`), or whatever survives filtering. It's not a shortcut worth taking. Go straight to LLM-generated instructions.
- **LLM-instruction regen cost: ~$0.15 / 1000 pairs.** Negligible. Should be the default from the start of every new modality.

## Data

- **Author-paired matched-style data is scarcer than planned.** HuggingFace deprecated `trust_remote_code` for script-based datasets (pg19, tldr-17 both broken). IMSDb URLs need careful URL-encoding (spaces, commas). Miller Center works. Gutenberg works but has curation failures (bad book_ids, non-English content, non-PD authors labeled wrong).
- **Minimum viable data: ~1000 pairs gives signal of mechanism but not of style match.** Text-001 at 971 pairs: T1 PASS (mechanism works) but T3 FAIL (style not learned). Real style transfer probably needs ≥10k. Plan for this in any new modality.
- **Register diversity matters for stratified eval.** Text-001 had 4 registers (poetry, essay, speech, screenplay) — helps make T3-style probes span different style axes. For audio/music/video, analogous register diversity should be planned from day one.
- **Author-disjoint splits are mandatory.** `tests/test_register_splits.py` enforces this at pair-construction time. Validated catching it — in experiment 001 our val authors never overlapped with train authors, which kept T1 meaningful.
- **Three-layer content-leak firewall works.** Paragraph MinHash filter at pair time + target-only instruction generation + 5-gram reject in instruction gen → 0% content leak observed at step 2000 of experiment 001. Portable to other modalities (adapt to modality-appropriate similarity metric).

## Architecture

- **Prefix-K/V injection into a frozen LM works mechanically.** Monkey-patching the attention forward for target layers, prepending projector K/V after RoPE, extending the additive mask. Observed at experiment 001: adapter alive (T1 PASS), no crashes, loss drops smoothly.
- **GQA-aware projector shape is non-optional.** Output must match `config.num_key_value_heads`, not `num_attention_heads`. Read at runtime; don't hardcode.
- **Zero-init projector output = training starts as a no-op.** Confirmed: step-0 adapter output ≈ step-0 no-ref output. The adapter mechanism should always begin inert.
- **RoPE on content K only (prefix K unrotated) is the right choice.** Prepending after `apply_rotary_pos_emb` for content K lets prefix positions act as positionless controllers.
- **KV cache + prefix injection is non-trivial.** Attention mask size mismatches on decode steps. `use_cache=False` during generate is the pragmatic workaround; proper fix is future work.
- **Encoder bottleneck underspecifies style at 16 queries.** Open hypothesis, evidence from 001. Possible fixes: 32-64 queries, contrastive loss on encoder outputs, wider ref encoder.
- **Multimodal base models have nested paths.** Gemma-3-4B loads as `Gemma3ForConditionalGeneration` with text tower at `.model.language_model.layers`. Budget a day to figure out the paths for any new base model. Also: 400 MB of vision tower weights are loaded-but-unused — drop them at load time for ~10% memory savings.

## Eval

- **T1 discrimination is a necessary-but-not-sufficient test.** Adapter-vs-swap Jaccard → 0 at step 2000 of 001, yet T3 style carryover FAIL'd. The adapter can produce different outputs per reference without those outputs being style-matched. So T1 PASS alone doesn't mean the adapter works.
- **T2 (vs prompted_baseline) is the load-bearing gate — but CAN fire spuriously from register bias.** Experiment 002 passed T2 at 80% via LLM judge but its conditioning-pathway diagnostic (003) showed near-zero reference-specific signal — the adapter learned "produce literary register" not "condition on THIS reference." T2 alone is insufficient to validate C1; must be paired with T3b (LLM-judge style match) AND at least one pathway probe.
- **T2/T3 verdicts at n<20 are unreliable.** 001's n=4 TIE flipped to n=20 FAIL on the same data. Need n≥20 probes and evaluation at intermediate checkpoints to distinguish noise from regression.
- **T3 surface-feature metrics are broken across experiments at our scale.** Replaced with LLM-judge T3b (directly asks Claude "which generation matches the reference's style?"). Cheaper ($0.02/run at n=20) and categorically more informative.
- **Conditioning-pathway probes (cos_z / cos_K/V / gen_Jaccard across pathological references) are the load-bearing diagnostic.** These localize where in the encoder→projector→injection→output chain the signal dies. Experiment 003 showed the encoder works but the projector collapses signal — an insight that pure training-loss-style analysis would never surface. Every training experiment from 003 onward should be paired with a post-training pathway probe.
- **Capability tests (α-blending, strength-dial) are more diagnostic than quality tests at small scale.** Because the architectural claim is about affordances prompting can't replicate. At any scale, if α-blending produces garbage rather than interpolation, the latent space isn't continuous — the program has a fundamental issue, regardless of how good T2 looks. With a collapsed projector, α-blending would produce identical outputs for any α — good canary.

## Architecture (updated after 004)

- **Contrastive loss on projector K/V outputs is a viable lever for breaking projector collapse.** Experiment 004 dropped average cos_K/V from 0.91 to 0.41 across pathological references (-0.50 swing) using contrastive_weight=0.1 alongside next-token CE. Confirms that the projector's degenerate "near-constant function" minimum is reachable from the regular minimum via a targeted decorrelation pressure. The fix is loss-landscape, not architecture.
- **Gradient flow through the projector improves the encoder for free.** Adding contrastive pressure to projector K/V outputs caused encoder cos_z to drop from 0.77 to 0.40 for swap variants, even with no direct pressure on z. The full pathway co-trains.
- **Contrastive loss has a real cost.** T2 vs prompting dropped from 002's 70% to 004's 60% — contrastive term competes with NTL. Worth it for the K/V gap but the trade-off is empirically meaningful, not negligible.
- **Reference-channel saturation around λ=1.** Strength-dial probe in 004 showed the prefix has a "loud enough" threshold near its trained operating point — λ=2 doesn't produce proportionally stronger conditioning. C4 should be reframed from "smooth continuous strength" to "thresholded conditioning depth."
- **α-blend supports monotonic interpolation in 6/8 probes.** Directional positive evidence for C3 (composability) at the textual-Jaccard level, though we don't yet know if the interpolation is along the style axis specifically (need an LLM-judge α-blend probe to verify).

## Architecture (updated after 003)

- **Shared-trunk projector collapses encoder diversity.** Experiment 003 diagnosed: encoder produces cos_z 0.0-0.77 across pathological references (good); projector output K/V stays cos 0.77-0.98 across the same inputs (bad — near-constant). Next-token CE training pressure pushes the shared MLP trunk toward a single "literary register" transform rather than a reference-specific transform. **Hypothesis**: per-layer heads reading z directly (no trunk) may fix this structurally; contrastive loss on K/V outputs may fix it via loss signal. Test both.
- **The base model is very sensitive to small K/V changes.** In 003, zero-prefix generation differs by gen_Jaccard=0.003 from own-reference generation despite 91% K/V cosine similarity on layer 1. This means the downstream stack (injection → base attention → generation) works fine; the failure is specifically at the projector's output diversity. A small improvement in projector output variance should produce large improvements in output reference-sensitivity.

## Infrastructure / ops

- **Experiment-tracking monorepo shape**: `core/` (shared, evolving, SHA-pinned per experiment) + `modality/` (specializations) + `experiments/<id>/` (immutable snapshots) + `site/` (MkDocs Material) + `tools/` (scaffold/build/replicate scripts) + `program/` (cross-project thesis + learnings + roadmap).
- **Three-layer metadata: experiment / project / program.** Each has its own LEARNINGS.md. Learnings cascade up periodically.
- **RunPod via runpod-lifecycle works well.** `Pod.open_ssh_client()` for paramiko SFTP, `setsid bash -c '... > log 2>&1' < /dev/null` for reliable backgrounding over SSH. Budget one 4090 (~$0.69/hr) per concurrent experiment.
- **`pip install -e .` on pod needs `allow-direct-references = true` in `pyproject.toml`** for any file:../ sibling dependency. Use `[project.optional-dependencies].infra` so pod installs can skip orchestration-only deps.
- **HF `trust_remote_code` is officially retired.** Script-based datasets (`deepmind/pg19`, `webis/tldr-17`, and many older academic datasets) are unavailable. Plan around this: use URL-fetched data or find already-converted Parquet equivalents.

## Process

- **Light megaplan is the right tool for scaffolding.** A 10-minute plan/critique/revise/execute loop produced a clean monorepo scaffold in one pass. Standard/robust is overkill for greenfield structure work.
- **Background subagents are fragile for multi-phase CLI orchestration.** Several times subagents quit prematurely mid-phase. For anything with sequential CLI calls (like megaplan workflow), either drive the CLI directly or chain phases via `&&` in a single `run_in_background` bash call.

## Auto-rollup (2026-04-25)

- **[2026-05-text-005-stronger-contrastive](../experiments/2026-05-text-005-stronger-contrastive/) — refuted**: Hypothesis REFUTED. T3b regressed 55%->50%, LLM-judge alpha-blend signal inverted +0.25->-0.25, pathway cos_K for same-domain refs got WORSE (swap 0.31->0.69, code 0.33->0.69). T2 actually improved 60%->65%. Projector responds non-monotonically to contrastive weight; more pressure is not the answer. Next

## Auto-rollup (2026-04-25)

- **[2026-05-text-006-projector-no-trunk](../experiments/2026-05-text-006-projector-no-trunk/) — partially_confirmed**: Architectural fix is real at the K/V pathway (cos_K_first_swap 0.69→0.22). Initial Haiku-judged T3b/α-blend looked decisive (16/20, signal 1.0) but Opus cross-judge revealed ~20% mode collapse and non-monotonic α-curve. Haiku is an unreliable style judge (rewards Gutenberg-surface markers over actual style-match). Key meta-learning: **dual-judge eval (Haiku + Opus or Sonnet) is required for any LLM-judge criterion**.

## Auto-rollup (2026-04-25)

- **[2026-05-text-010-v3-no-trunk-warmstart](../experiments/2026-05-text-010-v3-no-trunk-warmstart/) — partially_confirmed**: Repaired v3 plus no-trunk warmstart is pathway-positive but generation-quality-negative. Legacy n=20 `cos_K_last_swap=0.342`; v3 balanced n=20 `cos_K_last_swap=0.464` with random/code low, so global projector collapse is not the immediate blocker. Final samples remain repetitive and generic. The legacy probe omitted speech; the new balanced probe exposed register-specific weakness: screenplay separates strongly, essay/poetry are partial, and speech own-vs-swap is nearly collapsed (`cos_K_last_swap=0.883`). Next best bet is v3.1 data/eval repair, not wider encoder.

## Auto-rollup (2026-04-25)

- **[2026-05-text-013-v3.3-corrected-poetry-core3-smoke](../experiments/2026-05-text-013-v3.3-corrected-poetry-core3-smoke/) — partially_confirmed/data-positive-quality-negative**: The data audit found a root cause in bogus Gutenberg poetry IDs; corrected v3.3 core3 passed gates and removed known poetry contamination markers. The 1,500-step smoke stayed pathway-positive (`cos_K_last_swap=0.398`, random=-0.039, code=0.044), so reference signal propagates. Final generations still repeat across poetry/screenplay/speech, so the next best bet shifts from data hygiene to objective/decoding ablations. Do not full-run v3.3.

## Auto-rollup (2026-04-25)

- **[2026-05-text-014-objective-ablation-core3](../experiments/2026-05-text-014-objective-ablation-core3/) — refuted**: Disabling contrastive on corrected v3.3 core3 did not fix repetition and substantially worsened pathway separation (`cos_K_last_swap=0.792`, `cos_K_first_swap=0.861`, `cos_z_swap=0.720`). 013 with contrastive on had much healthier separation (`cos_K_last_swap=0.398`). Keep contrastive enabled; the next best bet is a decoding-control diagnostic on the 013 checkpoint before another training run.

## Auto-rollup (2026-04-25)

- **[2026-05-text-015-decoding-repetition-diagnostic](../experiments/2026-05-text-015-decoding-repetition-diagnostic/) — partially_confirmed**: Holding the 013 checkpoint fixed and changing only decoding controls almost eliminated mechanical loops. 013 adapter `repeat_3` was poetry=0.806, screenplay=0.261, speech=0.416; 015 sampled anti-repeat reduced `repeat_3` and repeated-line rate to 0.0 across all three registers. This makes decoding a real eval lever, but not a claim win: instruction leakage, page artifacts, generic/no-ref contamination, and uncertain author-level style carryover remain. Next best bet is a small judge/human audit of 015 sampled outputs before another training run.

## Auto-rollup (2026-04-26)

- **[2026-05-text-017-v3.4-artifact-clean-core3-smoke](../experiments/2026-05-text-017-v3.4-artifact-clean-core3-smoke/) — partially_confirmed**: v3.4 artifact cleanup preserves the healthy contrastive-on pathway while materially improving sampled generations. Pathway: `cos_K_last_swap=0.502`, random/code near zero or negative. Sampled adapter outputs: `repeat3_mean=0.002`, repeated-line mean `0.0`, T1 PASS (`mean_jaccard=0.004`), T4 PASS/PASS (`0%` target memorization/reference leak), T5 SLOW. Manual read is register-positive but not yet author-style-proven; residual screenplay/poetry artifacts remain. Next best bet is a longer v3.4 run with contrastive on and n>=20 dual-judge T2/T3b.

## Auto-rollup (2026-04-26)

- **[2026-05-text-018-v3.5-strict-artifact-clean-core3-longer](../experiments/2026-05-text-018-v3.5-strict-artifact-clean-core3-longer/) — inconclusive_negative**: v3.5 fixed a real missed artifact class in v3.4 (wrapped Gutenberg picture/note blocks), and sampled generations stayed clean (`repeat3_mean=0.001`). But the longer continuation plateaued and showed same-register pathway collapse risk on the n20 default probe (`cos_K_last_swap=0.909`), with T4 WEAK/WEAK at 10% each. Also found an eval design bug: `build_default_probes(n=20)` can select mostly two authors per register and repeat author pairs. A balanced n21 probe is now persisted; next best bet is checkpoint comparison on balanced n21, not another long train.

## Auto-rollup (2026-04-26)

- **[2026-05-text-019-balanced-checkpoint-comparison](../experiments/2026-05-text-019-balanced-checkpoint-comparison/) — completed**: Balanced n21 corrected the skewed n20 interpretation. `018_step1000` is the best checkpoint (`cos_K_last_swap=0.609`, random=-0.114, code=-0.070, surface T3 WEAK 13/21), but the dominant blocker is speech: speech `cos_K_last_swap` stays around `0.97` for every checkpoint, while poetry+screenplay mean is best at `0.428`. T4 `WEAK` warnings are mostly formulaic speech salutations, not strong target memorization evidence. Next best bet is a core2 no-speech smoke before wider encoder.

## Auto-rollup (2026-04-26)

- **[2026-05-text-020-core2-no-speech-smoke](../experiments/2026-05-text-020-core2-no-speech-smoke/) — partially_confirmed**: Removing speech was the right diagnostic. The core2 run passed the pathway gate (`cos_K_last_swap=0.440`, random=-0.149, code=-0.066) and T4 is clean (`0%` memorization/leak), so speech was masking a healthier poetry+screenplay pathway and creating false-positive leakage. But the aggregate is carried by screenplay (`cos_K_last_swap=0.248`); poetry remains weak (`0.633`) and surface T3 is only WEAK (`11/20`). Next best bet is core2 data/eval repair, not wider encoder: strip screenplay page/image artifacts and audit poetry author-pair separability before another training run.

## Auto-rollup (2026-04-26)

- **[2026-05-text-021-core2-eval-data-repair](../experiments/2026-05-text-021-core2-eval-data-repair/) — completed**: v3.7 repaired screenplay train artifacts and made core2 probes use unique heldout refs where possible. `020_final` remains best (`cos_K_last_swap=0.502`, random=-0.071, code=-0.091) over `018_step1000` (`0.598`), with T1/T4 clean and low repetition. But the repaired probe overturns the simple "screenplay solved" story: poetry=`0.522`, screenplay=`0.483`, surface T3 still WEAK. Current heldout coverage is too narrow for strong C1 claims, and many better heldout authors are contaminated by warmstart training exposure. Next best bet is broader clean split/restart design plus dual-judge T2/T3b when a judge key is available.

## Auto-rollup (2026-04-26)

- **[2026-05-text-022-broader-clean-split-restart](../experiments/2026-05-text-022-broader-clean-split-restart/) — partially_confirmed**: The v3.8 clean-heldout restart removes 006 warmstart author overlap and still passes the pathway gate: aggregate `cos_K_last_swap=0.382`, poetry `0.293`, screenplay `0.470`, random/code `0.117`/`0.014`. Sampled anti-repeat outputs are low-repeat and T4-clean, but surface T3 remains WEAK and manual read is register-positive rather than author-style-proven. The current bottleneck is now style-quality evaluation/objective alignment, not global projector collapse or heldout contamination. Operationally, RunPod source/output should run from `/tmp` with `/workspace` treated as read-only data/checkpoint storage.

## Auto-rollup (2026-04-26)

- **[2026-05-text-023-evalclean-probe-audit](../experiments/2026-05-text-023-evalclean-probe-audit/) — negative_informative**: v3.9 rebuilt 022's probes with clean heldout target chunks as references (`dirty_refs=0`). This removed an obvious poetry confound, especially a repeated Christina Rossetti footnote reference, but did not rescue C1: aggregate `cos_K_last_swap` worsened from `0.382` to `0.541`, poetry worsened to `0.647`, while random/code remained separated (`0.047`/`-0.079`). The issue is not only dirty eval refs; clean same-register author-style binding is fragile. Next best bet is objective/data alignment: clean train references, less brittle instructions, and a direct own-vs-swap style/author-negative signal before wider encoder.

## Auto-rollup (2026-04-26)

- **[2026-05-text-024-v4-objective-data-repair](../experiments/2026-05-text-024-v4-objective-data-repair/) — partially_confirmed**: Continuations from 022 did not work (`0.522` on v3.9, `0.535` on v4), but restarting from the cleaner 006 no-trunk checkpoint on v4 with stronger triplet (`0.5`) and normal contrastive (`0.1`) produced the strongest clean pathway result so far: aggregate `cos_K_last_swap=0.360`, screenplay `0.161`, poetry `0.559`, random/code near zero. This confirms path-dependence from the old dirty instruction/data distribution. Still not C1: sampled T3 FAIL (`15/32`) and poetry remains weak. Next best bet is poetry-specific repair/objective, not wider encoder.

- **[2026-05-text-025-poetry-specific-style-axis](../experiments/2026-05-text-025-poetry-specific-style-axis/) — ready/blocked**: 025 is staged as a strict poetry-only restart from 006. v4.2 direct poetry-only data was built, but audit found many title/section headers and a dramatic swap reference; v4.3 is now the preferred dataset (`1,771` train rows, `378` val, `358` test, `16` generic probes, zero stage-keyword hits after filtering). Current blocker is operational: local Hugging Face auth is missing, so fresh Gemma pods 401. Token sync now accepts either `~/.cache/huggingface/token` or `HF_TOKEN`/`HUGGINGFACE_HUB_TOKEN`.
