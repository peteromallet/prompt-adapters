# Experiment 015 Analysis Summary

Status: completed on 2026-04-25.

## Result

The decoding-control diagnostic is **partially confirmed**.

Holding the 013 checkpoint fixed and changing only generation controls nearly
eliminated the mechanical repetition that made 013/014 samples unusable.

## Repetition Metrics

Adapter samples, same n=15 probe set:

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

Full metrics are in `results/repetition_metrics.json`.

## Qualitative

The sampled anti-repeat variant is the better candidate:

- poetry is much less looped, though one sample leaked instruction framing;
- screenplay produces coherent scene fragments without local beat loops;
- speech becomes fluent formal-address prose;
- no-ref remains generic or contaminated, preserving its negative-control role.

The result is promising but not sufficient. Anti-repeat decoding fixes the
obvious loop pathology, but it does not prove author-level style carryover.

Follow-up local eval on the sampled variant:

- T1 reference discrimination: PASS (`mean_jaccard=0.002`)
- surface-feature T3: WEAK (`own_wins=7/15`)
- memorization: WEAK (`6.7%`)
- reference leak: PASS (`0.0%`)
- LLM judges: skipped locally because `ANTHROPIC_API_KEY` was not set

Manual audit estimated `10/15` sampled adapter outputs as broadly acceptable:
poetry `2/5`, screenplay `4/5`, speech `4/5`. Details are in
`results/manual_sampled_audit.md`.

## Decision

Use sampled anti-repeat as the default eval profile for the next comparison:
`do_sample=True`, `temperature=0.8`, `top_p=0.9`,
`repetition_penalty=1.12`, `no_repeat_ngram_size=3`.
The profile is persisted at
`text-ip-adapter/configs/decoding_sampled_antirepeat.yaml`.

Next best bet: run a small judge/human audit on 015 sampled outputs versus 013
original outputs. If style carryover remains weak, keep contrastive enabled and
change the training target/objective next.
