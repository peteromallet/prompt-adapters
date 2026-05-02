# Learnings

Status: completed; pathway-positive, surface-mixed.

024c showed screenplay pathway strength (`cos_K_last_swap=0.161`) but poetry
weakness (`0.559`). Qualitative poetry samples from 024c are not yet
convincing: several generations start with all-caps titles, one probe produced
plain prose about proofreading a first draft, and the old v4 probe source still
contained brittle heading/dramatic material.

Local follow-up work:

- Built `pairs_v4_2_poetry_styleclean`: direct poetry-only v4.1 slice, 1,795
  train rows, 387 val rows, 359 test rows, 16 generic probes.
- Audited v4.2 and found the probe set had generic instructions, but one swap
  reference was dramatic verse headed `BURR`; many train/val rows carried
  uppercase title/section headings.
- Built preferred `pairs_v4_3_poetry_strict`: 1,771 train rows, 378 val rows,
  358 test rows, 16 probes, all poetry, zero stage-keyword hits after cleaning,
  and 477 train rows with headings stripped.
- Added `stage1_v4_3_poetry_strict_triplet_restart006.yaml` as the next launch
  config.
- Patched HF token sync to accept `HF_TOKEN` or `HUGGINGFACE_HUB_TOKEN` in
  addition to `~/.cache/huggingface/token`.

Next scientific claim to test: if v4.3 still leaves poetry weak, the blocker is
probably not broad corpus contamination; move to a stronger style-supervision
objective rather than more data cleaning.

Outcome: v4.3 did not leave the pathway weak. The repeat run got
`mean_cos_K_last_swap=0.4053`, down from 024c poetry `0.5592`, with random/code
still separated (`0.1012`/`0.1387`). That nearly hits the `<=0.40` target and
validates strict poetry isolation plus triplet pressure as a real pathway
improvement.

But sampled outputs are still not claim-ready. Repetition is low
(`repeat3_mean=0.0050`, line repeats `0.0`), and some outputs are credible
verse, but there is residual instruction/meta leakage and prose drift. Examples:
`edna_millay_01`, `emily_dickinson_01`, `sara_teasdale_00`, and
`stephen_crane_00`.

Next best bet: keep the v4.3 strict poetry data, but add stronger
style-supervision or surface-quality pressure. Do not spend another cycle on
generic broad data cleaning before addressing the leakage/alignment failure.

Manual cleanup follow-up changed that slightly. v4.4 removed 553 bad rows and
edited 83 rows, but structural audit showed the cleaned splits were still
reference-poor and duplicate-heavy: train had 1,268 rows but only 37 unique
references, val had 348 rows but only 7 unique references, test had 339 rows
but only 6 unique references, and the probe set dropped to 15 rows after one
bad Masefield probe was removed.

Built `pairs_v4_5_poetry_structural_balanced` as the next fair test. It keeps
the manual cleanup, dedupes exact target text, caps repeated references, caps
train author overrepresentation, and rebuilds balanced 16-row probes. Result:
727 train rows, 183 val rows, 134 test rows, zero target duplicate groups, max
repeated reference 40 train / 30 heldout, and 16 probes with 2 per heldout
author.

Updated next best bet: run v4.5 with the same v4.3 triplet restart objective.
This isolates whether v4.3's good pathway / mixed surface result was partly
propped up by repeated-reference exposure. If v4.5 keeps the pathway gain and
improves surface quality, continue with structurally balanced poetry. If it
keeps pathway gain but surface leakage remains, move to stronger surface/style
supervision. If it degrades, the real missing ingredient is more clean unique
poetry, not more pair expansion.

v4.5 run result: pathway stayed positive but softened. `mean_cos_K_last_swap`
was `0.4340`, worse than v4.3 repeat `0.4053` but still much better than 024c
poetry `0.5592`; random/code were cleanly separated (`-0.0650` / `0.0173`).
Sampled adapter rows had no crude explicit meta hits and no 3-gram repetition,
but qualitative failures remain: some outputs are prose-like, placeholder-like,
or quote/essay drift. This supports a narrower conclusion: structural cleanup
improves eval hygiene and maybe surface cleanliness, but the next real lever is
stronger surface/style supervision or more unique clean poetry for thin authors,
not more duplicate pair expansion.
