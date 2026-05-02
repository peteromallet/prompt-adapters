# Experiment 015 - decoding repetition diagnostic

Status: completed on 2026-04-25.

## Question

Are the repeated generations after 013 primarily a decoding-time failure?

## Hypothesis

013 showed a healthy contrastive-on pathway but poor repeated samples. 014
showed that removing contrastive does not fix repetition and hurts the pathway.

The cheapest remaining split is checkpoint-fixed decoding: keep the 013
checkpoint, data, probes, and model fixed, then rerun generation with explicit
anti-repetition controls.

## Method

- Use the 013 checkpoint:
  `checkpoints/stage1_v3_3_corrected_poetry_core3_smoke/final.pt`.
- Use the 013 config and balanced n=15 probes.
- Run checkpoint-only eval on a fresh RunPod, no training.
- Compare two variants:
  - `greedy_no_repeat`: deterministic decoding plus `repetition_penalty=1.15`
    and `no_repeat_ngram_size=3`;
  - `sampled_rep`: sampled decoding with `temperature=0.8`, `top_p=0.9`,
    `repetition_penalty=1.12`, and `no_repeat_ngram_size=3`.

## Decision Rule

Promote decoding controls only if they visibly reduce loops in all three
registers without making outputs generic or erasing own-vs-swap contrast.

If controls fail, the next experiment should change target construction or the
training objective directly.

## Result

The decoding hypothesis is partially confirmed.

Both anti-repetition variants removed the obvious mechanical loops from 013.
The sampled variant is generally the stronger qualitative candidate: it keeps
longer outputs and often produces plausible verse, screenplay, and formal
speech shapes.

Adapter repetition metrics on the same n=15 probe set:

| run | register | repeat_3 | repeat_line |
| --- | --- | ---: | ---: |
| 013 original | poetry | 0.806 | 0.637 |
| 013 original | screenplay | 0.261 | 0.261 |
| 013 original | speech | 0.416 | 0.207 |
| 015 greedy no-repeat | poetry | 0.005 | 0.000 |
| 015 greedy no-repeat | screenplay | 0.000 | 0.000 |
| 015 greedy no-repeat | speech | 0.000 | 0.000 |
| 015 sampled anti-repeat | poetry | 0.000 | 0.000 |
| 015 sampled anti-repeat | screenplay | 0.000 | 0.000 |
| 015 sampled anti-repeat | speech | 0.000 | 0.000 |

Residual problems remain:

- sampled poetry can leak instruction framing;
- screenplay can contain odd page-number artifacts;
- no-ref controls remain generic or contaminated;
- style quality still needs a judge or focused human audit.

Local non-LLM eval on the sampled variant gave T1 PASS, surface-feature T3 WEAK
(`7/15` own wins), memorization WEAK (`6.7%`), and reference leak PASS. LLM
judges were skipped because `ANTHROPIC_API_KEY` was not set locally.

Manual audit judged roughly `10/15` sampled adapter outputs broadly acceptable:
poetry `2/5`, screenplay `4/5`, speech `4/5`.

## Decision

Anti-repetition decoding is a real lever and should be formalized for
evaluation. It does not by itself prove that style carryover is good.

Next best bet: run a small judge/human audit comparing 013 original versus 015
sampled anti-repeat on the same probes. If style carryover is still weak, keep
contrastive on and change target construction or training objective directly.
