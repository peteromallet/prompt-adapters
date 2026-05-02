# Experiment 009 - v3 data rebuild speechfix

Status: planned

## Question

Can we rebuild the text style-transfer corpus so speech author diversity and
per-register held-out coverage are real before launching another GPU run?

## Hypothesis

The v2/v2_bundle failures are primarily corpus-construction failures, not a
lack of source material:

- v2 speech used congressional floor fragments under `un_debate`, which is the
  wrong speech style source for this objective.
- the old Miller Center speech path had a parser bug: global nav anchors caused
  every cached speech page to be labeled `washington`.
- `v2_bundle` recovered pathway discrimination because the no-trunk warmstart
  recipe is viable, but the data split remained invalid for clean validation.

If the Miller Center author extraction is fixed and the pair builder enforces
per-register split minimums, the corpus should produce enough speech pairs to
train and evaluate without using congressional fragments as a proxy.

## Method

1. Use the patched `text_ip_adapter.data.ingest_speeches` implementation:
   infer president from the Miller Center speech URL date and do not use global
   nav `/president/*` anchors as author metadata.
2. Re-ingest cached Miller speech pages with `SPEECHES_MAX=1000`.
3. Generate speech pairs at several per-author caps.
4. Choose the smallest cap that clears:
   - train speech >= 1500 pairs
   - val speech >= 100 pairs
   - test speech >= 100 pairs
   - >= 30 speech authors overall
5. Replace the global author split in the v2 builder with per-register author
   split gates:
   - every scoped register must appear in train/val/test
   - val/test must each have configured minimum pairs per register
   - failure exits non-zero, not a warning
6. Build a candidate `data/pairs_v3/` corpus only after source and split gates
   pass.

No GPU training is part of this experiment.

## Results

Candidate v3 build passed hard gates.

| split | rows | poetry | essay | screenplay | speech |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 10,730 | 2,944 | 144 | 5,708 | 1,934 |
| val | 310 | 100 | 100 | 60 | 50 |
| test | 310 | 100 | 100 | 60 | 50 |

Artifacts:

- `results/v3_candidate/train.jsonl`
- `results/v3_candidate/val.jsonl`
- `results/v3_candidate/test.jsonl`
- `results/v3_candidate/manifest.json`

Known caveat: held-out authors are sparse for poetry/essay/speech because the
capacity-aware split is designed to guarantee pair coverage with scarce
registers. This is a valid next training corpus, not a final eval corpus.

## Learnings

See `LEARNINGS.md`.

## Replicate

Use the current pod with cached Miller Center HTML:

```bash
cd /workspace/text-ip-adapter
PYTHONPATH=src SPEECHES_MAX=1000 python scripts/fetch_data.py
```

Final v3 builder command:

```bash
cd /workspace/text-ip-adapter
PYTHONPATH=src python scripts/build_v3_pairs.py \
  --output-dir data/pairs_v3_candidate \
  --cap speech=50 \
  --cap poetry=100 \
  --cap essay=100 \
  --cap screenplay=30 \
  --max-speeches 1000 \
  --instruction-mode generic \
  --min-heldout-per-register 50 \
  --speech-train-min 1500
```
