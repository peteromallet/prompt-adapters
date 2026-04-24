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
