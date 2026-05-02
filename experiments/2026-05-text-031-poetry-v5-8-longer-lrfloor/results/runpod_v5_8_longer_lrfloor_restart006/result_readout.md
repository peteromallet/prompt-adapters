# Result readout: exp031 / v5.8 longer LR-floor training

Status: completed. Train artifacts were intentionally skipped; eval artifacts and logs were
downloaded and the pod terminated cleanly.

## Question

Does v5.7 pair-audited data need more effective training time, once the LR schedule stops decaying
to nearly zero?

## Change from exp030

Data and objective stayed fixed:

- train split: `pairs_v5_7_poetry_pair_audited_min25`
- train rows: 3,135
- train authors: 47
- `style_triplet_weight`: 1.5
- `contrastive_weight`: 0.2
- warm-start: `checkpoints/stage1_gemma_no_trunk/final.pt`

Training schedule changed:

- `max_steps`: 1,200 -> 2,400
- `min_lr_ratio`: 0.0 -> 0.10

This made the run a real longer-training test. Exp030 ended with projector LR around `1.17e-8`;
exp031 ended around `1.00e-6`.

## Pathway metrics

- `mean_cos_K_last_swap`: 0.0504
- `mean_cos_V_last_swap`: 0.0446
- `mean_cos_z_swap`: 0.3877
- `mean_gen_jaccard_swap`: 0.0707
- `mean_cos_K_last_random`: -0.0710
- `mean_cos_V_last_random`: -0.0611
- `mean_cos_K_last_code`: 0.0311
- `mean_cos_V_last_code`: -0.0179

Comparison:

- v5.4/exp028: `K_last_swap=0.2123`, `V_last_swap=0.1925`
- v5.5/exp029: `K_last_swap=0.1711`, `V_last_swap=0.1470`
- v5.7/exp030: `K_last_swap=0.1231`, `V_last_swap=0.1048`
- v5.8/exp031: `K_last_swap=0.0504`, `V_last_swap=0.0446`

This is the strongest pathway result so far, and the random/code controls did not inflate.

## Sampled qualitative read

Sampled eval wrote 48 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`, and
`prompted_baseline`.

- `adapter`: median 284.5 chars, meta hits 0, QA hits 0, max repeat-3 = 1.
- `adapter_swap`: median 145.5 chars, meta hits 0, QA hits 0, max repeat-3 = 1.
- `no_ref`: median 478.5 chars, meta hits 4, QA hits 1, max repeat-3 = 1.
- `prompted_baseline`: median 397.0 chars, meta hits 4, QA hits 2, max repeat-3 = 2.

Qualitative verdict: mixed. The adapter remains much cleaner than no-ref and prompted baseline:
less instruction/prose leakage and no mechanical repetition. But it still does not reliably write
strong author-specific poetry. Several outputs are generic nursery/garden verse, narrative prose
broken into lines, or wrong-style imitation. There are still training-data style ghosts such as
didactic prose and generic "sun/birds/flowers" verse.

Examples of remaining failure modes:

- Newman adapter generated prose about imitating authors rather than a poem.
- Wordsworth adapter generated a compressed archaic prose/quote block.
- Kemp adapter drifted into plain narrative prose.
- Some probe generations in pathway eval still collapse into generic repeated nature lines.

## Conclusion

The data/train-time balance answer is now clearer:

- More effective training helped the conditioning pathway materially.
- The qualitative bottleneck is not solved by pathway separation alone.
- The next best bet is not another longer run on the same pair set.

Exp031 says we can route reference-conditioned signal very strongly. The remaining problem is the
training target/data distribution and generation-facing alignment: the adapter learns "poem-ish
artifact space" more reliably than distinctive author style.

## Next best bet

Do a data-quality expansion and target-style tightening pass before the next full training run:

1. Build a larger source-native corpus with stricter row-level filters for prose, headings, OCR,
   instructional text, and generic anthologized children's verse.
2. Rebuild pair selection to prefer high-style, medium-length, internally coherent poems and to
   avoid pairing wildly inconsistent same-author rows.
3. Add a heldout qualitative audit focused on author distinctiveness, not just artifact removal.
4. Then rerun the exp031 recipe on the new corpus, preserving the final checkpoint for eval-only
   prompt/decoding sweeps.

