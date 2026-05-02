# Result readout: exp027 / v5.2 heldout-clean restart006

Status: training, pathway eval, and sampled eval completed. The wrapper failed only during local
train-artifact download because the laptop disk filled while pulling `final.pt`; eval artifacts
were already downloaded and the pod was terminated.

## Pathway metrics

- `mean_cos_K_last_swap`: 0.2471
- `mean_cos_V_last_swap`: 0.2586
- `mean_cos_z_swap`: 0.5599
- `mean_gen_jaccard_swap`: 0.0894
- `mean_cos_K_last_random`: 0.0523
- `mean_cos_K_last_code`: 0.1302

Interpretation: v5.2 is still well away from v2/v4 collapse, but it is weaker than v5.0 on
the main pathway metric (`mean_cos_K_last_swap`: v5.0 0.1500 vs v5.2 0.2471).

## Sampled qualitative read

Sampled eval wrote 48 rows: 12 each for `adapter`, `adapter_swap`, `no_ref`, and
`prompted_baseline`.

- `adapter`: median 124.5 chars, no meta hits, max repeat-3 = 1.
- `adapter_swap`: median 144.5 chars, no meta hits, max repeat-3 = 1.
- `no_ref`: median 454 chars, 4 meta/instruction hits, max repeat-3 = 2.
- `prompted_baseline`: median 270.5 chars, 3 meta/instruction hits, max repeat-3 = 2.

The adapter helps: adapter-conditioned generations are poem-like and avoid the instruction/meta
junk seen in no-ref/baseline. But they remain short, generic, and sometimes prose-like. This is
not yet a solved generation surface.

## Data audit prompted by this run

v5.2 probes were cleaner than v5.1, but spot-checks still found source-native artifacts in
the corpus and heldout pairs:

- table-of-contents/page-list rows, especially Tennyson/Wordsworth/Hardy-style collected editions;
- prefaces/editorial introductions, including Hardy and Dickinson;
- publisher/review/ad matter, especially IA scans;
- commentary/translation-heavy material in the Pope Leo XIII bucket.

This invalidates the earlier "audit pass" as sufficient: the deterministic audit missed important
row classes. The next best bet is another data-only repair while keeping the objective fixed.

## Follow-up already staged

- `author_source_curation_v3_row_artifact_clean.json`: rejected 1,469 additional row artifacts.
- `author_source_curation_v4_probe_artifact_clean.json`: additionally dropped the Pope Leo XIII
  bucket and caught repeated italic title-list rows exposed by the v5.3 probe audit.
- `poetry_corpus_v0_source_native_curated_candidate_v13`: 18,664 rows, 65 authors, audit pass.
- `pairs_v5_4_poetry_corpus_probe_artifact_clean`: 3,859 train / 144 val / 144 test, duplicate-free.

Conclusion: do not scale data yet. Run the same training recipe on v5.4 first to isolate the
effect of the data repair.
