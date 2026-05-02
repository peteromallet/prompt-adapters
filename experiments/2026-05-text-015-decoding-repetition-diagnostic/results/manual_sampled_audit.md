# Manual Audit - 015 Sampled Anti-Repeat

Scope: adapter outputs only, sampled anti-repeat variant, n=15 balanced probes.

## Verdict

The sampled anti-repeat profile is a real improvement over 013, but not a final
quality solution.

Approximate manual acceptability:

| register | acceptable | notes |
| --- | ---: | --- |
| poetry | 2/5 | loop-free, but instruction/prose leakage remains severe |
| screenplay | 4/5 | mostly coherent screenplay shape; some page-number and odd-fragment artifacts |
| speech | 4/5 | fluent formal speech/public-address shape; some generic modern rhetoric |
| overall | 10/15 | much more usable than 013, still not claim-supporting |

## Register Notes

Poetry is the weakest register. `v31_poetry_00` and `v31_poetry_04` are
plausible verse-shaped outputs. `v31_poetry_01` leaks instruction framing
instead of writing the target. `v31_poetry_03` becomes prose summary. This says
decoding fixed loops but did not fix the poetry target/instruction boundary.

Screenplay is the strongest register. Most samples are recognizably screenplay
fragments with scene headers, character/action formatting, and no local loops.
Residual artifacts include stray page numbers (`504.`, `278.`) and occasional
garbled fragments.

Speech is mostly fluent and register-correct. Several outputs have plausible
formal openings and period-public-address cadence. The weakness is genericity:
some outputs sound like generic presidential rhetoric rather than clearly
author-specific style.

## Decision

Do not launch another GPU training run yet.

The next step is an explicit style-quality audit. The sampled decoding profile
should be treated as the evaluation default for that audit, because the old
deterministic profile mostly measured decoding loops rather than style transfer.

If the style audit fails, the next training intervention should target
instruction/target construction:

- strip page-number artifacts from screenplay targets;
- filter poetry samples that are actually prose apparatus or prompts;
- make generation prompts harder to answer with instruction framing;
- consider shorter, cleaner target windows before architecture changes.
