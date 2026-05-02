# Pipeline Cleanup Report

Scope: `text-ip-adapter/scripts/build_v3_pairs.py`, `text_ip_adapter/eval/samples.py`, and the 015/016 experiment docs.
This report does not change shared pipeline code. It proposes the safest cleanup architecture and the exact gates the rebuilt manifests should enforce.

## Recommendation

Use a **manifest-first deterministic cleaning pipeline**:

1. Clean rows with fixed rules only.
2. Record every delete/quarantine reason in a machine-readable audit manifest.
3. Split only after the cleaned pool still satisfies heldout feasibility gates.
4. Rebuild probe manifests from the post-clean split, not from stale probe files.
5. Validate style claims only on the sampled anti-repeat profile from 015.

The key safety rule is: **never let cleaning silently consume the last usable heldout author or drop a register below its heldout floor**. Anything that threatens that becomes quarantine, not deletion.

## Ordered Implementation Plan

1. **Add row-level cleaning metrics to the builder manifest**
   - Track `input_rows`, `kept_rows`, `removed_rows`, `quarantined_rows`.
   - Break all metrics down by `register`, `author`, and `source_dataset`.
   - Record reasons separately for `ref_text`, `target_text`, and pair-level blocklist hits.
   - Keep `removed_by_reason` and `removed_by_register`, but add `kept_by_register` and `kept_authors_by_register` so over-filtering is visible.

2. **Make heldout feasibility an explicit gate before split**
   - Keep the current author-disjoint split model, but reject any cleaned pool that cannot satisfy heldout coverage.
   - Do not silently fall back to train-only for a register that was intended to participate in eval.
   - If a register is too small after cleaning, mark it `excluded_registers` with a reason in the manifest.

3. **Rebuild split and probe manifests from the cleaned pool**
   - Regenerate `train.jsonl`, `val.jsonl`, `test.jsonl`.
   - Regenerate `probes_balanced_n15.jsonl` for the 016 corpus from the cleaned heldout rows.
   - Keep the probe manifest keyed to the corpus tag so 015 samples remain a frozen comparator.

4. **Write validation reports next to the rebuilt corpus**
   - Add a human-readable validation summary and a JSON summary in the dataset output dir.
   - Add an experiment-side validation note under the 016 `results/` tree that cites the exact corpus manifest hash/tag used for the audit.
   - For 015/016 comparisons, keep the style audit report separate from the data-cleaning report.

5. **Use the 016 eval pipeline only after the data gates pass**
   - `samples.py` should continue to emit adapter, adapter_swap, no_ref, and prompted_baseline records.
   - The style audit should compare adapter vs swap vs prompted_baseline on the sampled anti-repeat profile, not on the old deterministic profile.

## Exact Gates

### Data-cleaning gates

- `source_dataset_present == true`
- `cleaning_pass == true` only if every retained register still has enough rows to support heldout split.
- `register_retention_floor`: each active register must keep at least `100` rows after cleaning, so `val` and `test` can each clear the current `50`-row heldout floor.
- `register_author_floor`: each active register must keep at least `3` distinct authors after cleaning, so `val` and `test` can each clear the current `2`-author heldout floor.
- `no_heldout_starvation`: no cleaning rule may remove the last viable heldout author for a register.
- `quarantine_over_delete`: if a deterministic filter would remove more than `20%` of a register or more than `50%` of a candidate heldout author’s rows, quarantine the rows instead of hard-deleting them.
- `essay_excluded_until_explicitly_revalidated`: keep essay out of the current core3-style audit path unless it independently clears the same split gates.

### Split gates

- `train_poetry_gte_1500`
- `train_screenplay_gte_1000`
- `train_speech_gte_700`
- `val_poetry_gte_50`, `val_screenplay_gte_50`, `val_speech_gte_50`
- `test_poetry_gte_50`, `test_screenplay_gte_50`, `test_speech_gte_50`
- `val_poetry_authors_gte_2`, `val_screenplay_authors_gte_2`, `val_speech_authors_gte_2`
- `test_poetry_authors_gte_2`, `test_screenplay_authors_gte_2`, `test_speech_authors_gte_2`
- `author_disjoint_train_val == true`
- `author_disjoint_train_test == true`
- `author_disjoint_val_test == true`

### Probe and eval gates

- `balanced_probes.rows == 15` for the current 016 audit set.
- `balanced_probes.by_register == {"poetry": 5, "screenplay": 5, "speech": 5}`.
- `swap_reference_author != author` and `swap_reference_register == register` for every probe.
- Style audit runs on `do_sample=True`, `temperature=0.8`, `top_p=0.9`, `repetition_penalty=1.12`, `no_repeat_ngram_size=3`.
- Treat `T3b >= 60%` as the minimum pass line for moving forward, and require a manual blinded check if the score is near the boundary.

## Where To Add Metrics

- In `build_v3_pairs.py`: per-register and per-author cleaning counts, quarantine counts, and post-clean split feasibility counts.
- In the written `manifest.json`: a single `audit` block that includes gate booleans, failures, and the exact thresholds used.
- In the probe builder: counts for probe rows, heldout split source, and swap-author diversity.
- In the 016 validation report: adapter/swap/no_ref/prompted_baseline summary, plus the chosen corpus manifest tag.

## Where To Rebuild Manifests

- `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/manifest.json`
- `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/train.jsonl`
- `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/val.jsonl`
- `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/test.jsonl`
- `text-ip-adapter/data/pairs_v3_3_corrected_poetry_core3/probes_balanced_n15.jsonl`

## Where To Put Validation Reports

- Data validation: `text-ip-adapter/data/.../manifest.json` plus a sibling markdown summary.
- Experiment validation: `prompt-adapters/experiments/2026-05-text-016-style-audit-after-decoding/results/`
  - one markdown summary for the style audit,
  - one JSON summary for machine checks,
  - one note that records the exact dataset manifest used.

## Bottom Line

The safest cleanup path is deterministic cleaning with a manifest trail, then split feasibility checks, then probe rebuilds, then sampled anti-repeat style audit. The hard stop is any rule that would shrink a heldout register below its author or pair floor.
