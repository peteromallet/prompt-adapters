# Experiment 012 - v3.2 boilerplate/objective cleanup

Status: planned

## Question

Can stricter boilerplate cleanup and no-theme style instructions remove the
repetition/metadata artifacts seen in 011 without killing register coverage?

## Hypothesis

011 showed healthy pathway separation but bad generations. The most obvious
remaining data artifacts are not subtle:

- every speech pair carried `Transcript` boilerplate;
- many speech targets were formal public-record messages, not spoken public
  addresses;
- some outputs learned dictionary/reference-book patterns for themes like
  `shilling` and `letter`;
- content-style themes can be too low-information.

If we strip transcript boilerplate, filter formal transmitted-bill/reference
artifacts, and switch to a no-theme instruction, the 1,500-step smoke should
preserve pathway separation while reducing these qualitative failures.

## Method

1. Rebuild v3.2 from raw cached sources.
2. Strip leading `Transcript` boilerplate from ref/target text.
3. Filter suspicious target patterns:
   - public-record transmission boilerplate;
   - dictionary/reference entries;
   - repeated 5-grams;
   - table-of-contents/index/chapter headings.
4. Use `content_style_no_theme` instruction:
   `Use the reference passage for style. Write a new passage on the same broad subject.`
5. Gate the corpus before any GPU work.
6. If gates pass, run the same 1,500-step smoke as 011 and final balanced n=20
   pathway probe.

## Haiku Pair Audit

The row-level audit tool is:

```bash
cd /workspace/text-ip-adapter
ANTHROPIC_API_KEY=... PYTHONPATH=src python scripts/audit_pairs_llm.py \
  --in-dir data/pairs_v3_2 \
  --out-dir data/pairs_v3_2_haiku_audited \
  --decisions-dir experiments/v3_2_haiku_pair_audit \
  --splits train val test \
  --model claude-haiku-4-5 \
  --workers 8
```

Smoke first:

```bash
ANTHROPIC_API_KEY=... PYTHONPATH=src python scripts/audit_pairs_llm.py \
  --in-dir data/pairs_v3_2 \
  --out-dir data/pairs_v3_2_haiku_audited_smoke \
  --decisions-dir experiments/v3_2_haiku_pair_audit_smoke \
  --splits train val test \
  --model claude-haiku-4-5 \
  --workers 4 \
  --max-pairs 50
```

The auditor emits one decision per row:

- `keep`: use as-is;
- `delete`: remove noisy or harmful row;
- `edit`: keep after simple boilerplate removal only.

Outputs:

- `experiments/v3_2_haiku_pair_audit/{split}.decisions.jsonl`
- `data/pairs_v3_2_haiku_audited/{split}.jsonl`
- `data/pairs_v3_2_haiku_audited/audit_manifest.json`

The script is resumable: rerunning with the same `--decisions-dir` skips rows
already present in the decisions JSONL.

## Results

Interim:

- CPU v3.2 gates passed after removing 667 suspicious pairs, mostly speech
  boilerplate.
- A 1,500-step smoke was launched and killed after step 1000 because qualitative
  samples regressed.
- `content_style_no_theme` is refuted for this setup: no-ref and adapter
  samples learn to echo "The passage should be written in the style..." style
  prompt boilerplate.
- Reference-side cleanup was still incomplete: `View Transcript` survived in
  speech references and appeared in generations.

Next action is not another GPU run. Run the Haiku pair audit and apply
keep/delete/edit decisions, then rebuild a v3.3 candidate.

## Learnings

Pending final writeup. Current working learning: deterministic regex filters
catch obvious bad targets, but row-level semantic audit is needed because
reference-side boilerplate and school/reference-book prose still leak through.

## Replicate
