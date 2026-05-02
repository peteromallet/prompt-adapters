# Learnings

## Pre-launch root cause

Experiment 008b showed the recipe can recover pathway discrimination on the
bundle, but the data is not clean enough to support a canonical claim.

The deeper speech audit found a second, older bug:

- current v2 speech uses `un_debate`/congressional fragments and is stylistically
  wrong for the intended public-speech register;
- old Miller Center speech was not actually author-diverse because the parser
  treated the first global nav `/president/washington` link as page metadata;
- after patching author extraction to infer president from the speech URL date,
  the existing pod cache yields 998 Miller records across 42 presidents.

Pair potential after the patch:

| speech cap per author | total pairs | train | val | test |
| ---: | ---: | ---: | ---: | ---: |
| 15 | 627 | 507 | 60 | 60 |
| 30 | 1,242 | 1,002 | 120 | 120 |
| 40 | 1,642 | 1,322 | 160 | 160 |
| 50 | 2,034 | 1,634 | 200 | 200 |
| 75 | 2,987 | 2,387 | 300 | 300 |

This means speech scarcity is not real at the next experiment scale. The next
work is a data build, not another GPU tweak.

## Candidate v3 build

`scripts/build_v3_pairs.py` now builds a CPU-only candidate corpus with:

- repaired Miller Center speech author extraction;
- per-register capacity-aware author splits;
- hard gates for held-out register coverage;
- consistent generic style instruction:
  `Write a piece in the style of the reference passage.`

The first all-register run failed only one gate: essay val had 6 pairs because
the random split assigned a low-capacity essayist to heldout. The builder was
then changed to assign heldout authors by pair capacity before filling train.

The second run passed all hard gates:

| split | rows | poetry | essay | screenplay | speech |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 10,730 | 2,944 | 144 | 5,708 | 1,934 |
| val | 310 | 100 | 100 | 60 | 50 |
| test | 310 | 100 | 100 | 60 | 50 |

Sources:

- poetry: `project_gutenberg`
- essay: `project_gutenberg`
- screenplay: `imsdb`
- speech: `miller_center`

All gates pass:

- author-disjoint train/val/test
- source_dataset present
- every register present in val/test
- speech train >= 1500

Artifacts:

- `results/v3_candidate/train.jsonl`
- `results/v3_candidate/val.jsonl`
- `results/v3_candidate/test.jsonl`
- `results/v3_candidate/manifest.json`

## Caveat

The candidate is valid for the next cheap training run, but not perfect:

- val/test use only one held-out author for poetry, essay, and speech, and two
  for screenplay;
- essay train remains small at 144 rows because clean Gutenberg essay source
  diversity is limited;
- the generic instruction policy removes topical prompt artifacts, but it also
  changes the task distribution relative to older rule-generated runs.

This is still a cleaner next experiment than v2/v2_bundle because the known
speech and split failures are fixed and every scoped register has heldout
coverage.
