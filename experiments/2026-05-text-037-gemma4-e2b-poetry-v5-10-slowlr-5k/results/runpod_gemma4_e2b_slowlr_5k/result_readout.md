# Exp037 Gemma4 E2B slow-LR continuation readout

Status: completed after manual eval resume; pod terminated.

Run:
- Base: `google/gemma-4-E2B`
- Init: exp035 final, 2000-step checkpoint
- Continuation: 5000 more steps
- LR: projector `4e-6`, encoder `2e-6`, cosine floor `0.25`
- Data: `pairs_v5_10_poetry_llm_style_medium_strong`
- Train rows: 2868

## Loss

The loss was stable but flat. Slow LR made updates gentler, but did not produce a visible descent.

Bucketed training loss:

| Steps | loss mean | loss sd | ntl mean | ntl sd |
| --- | ---: | ---: | ---: | ---: |
| 0-1k | 3.722 | 0.371 | 3.509 | 0.344 |
| 1-2k | 3.785 | 0.457 | 3.534 | 0.373 |
| 2-3k | 3.810 | 0.527 | 3.590 | 0.425 |
| 3-4k | 3.732 | 0.445 | 3.511 | 0.405 |
| 4-5k | 3.693 | 0.493 | 3.525 | 0.429 |

Projector norm changed slowly, ending around `1266.73`.

## Checkpoint metrics

Key comparisons:
- `adapter_prompted_vs_prompted_baseline`: does prompt + adapter beat prompt alone?
- `adapter_vs_adapter_swap`: does own reference beat another author's reference? This is the core style-binding test.
- `adapter_vs_no_ref`: does adapter beat no reference?

| checkpoint | K swap | V swap | z swap | adapter+prompt win / delta | own vs swap win / delta | adapter vs no-ref win / delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step 1000 | 0.189 | 0.031 | 0.235 | 0.500 / +0.016 | 0.417 / +0.023 | 0.667 / +0.141 |
| step 2000 | 0.157 | 0.059 | 0.213 | 0.750 / +0.122 | 0.333 / -0.019 | 0.667 / +0.168 |
| step 3000 | 0.122 | 0.041 | 0.185 | 0.667 / +0.076 | 0.417 / -0.025 | 0.583 / +0.016 |
| step 4000 | 0.095 | 0.005 | 0.164 | 0.500 / -0.037 | 0.667 / -0.011 | 0.583 / +0.133 |
| final | 0.094 | 0.017 | 0.165 | 0.833 / +0.052 | 0.417 / -0.024 | 0.500 / +0.018 |

## Subjective sample read

The run improves "poem-shapedness" relative to broken cold-start outputs, but does not convincingly learn style conditioning.

Observed issues:
- Own-reference generations are often prose, essay-like, or instruction-answering.
- Several outputs talk about writing a poem, analyze a poem, or include classroom/HTML artifacts.
- `adapter_prompted` often beats prompt-only in the pairwise heuristic, but this seems to be a generic quality/poetry nudge rather than reference-specific binding.
- Swapped-reference generations often look as good as, or better than, own-reference generations.
- Later checkpoints are not clearly better. Step 2000 is the best for prompt+adapter vs prompt-only; step 4000 is the only checkpoint with an own-vs-swap win-rate above 0.5, but its mean delta is still negative and samples remain contaminated.

Representative failures:
- Final Buchanan adapter output advertises a poetry activity book rather than writing in the reference style.
- Final Kemp adapter output asks for an essay about a quote.
- Step 4000 Buchanan adapter asks the user to write another poem.
- Step 3000 Dickinson adapter says "Here is what I wrote" and produces generic sentimental verse.

## Conclusion

Slow LR was worth testing, but it is not the lever. It stabilized the continuation without fixing the core failure.

The strongest conclusion is: the adapter can add a weak poetry/quality prior, but current training does not reliably bind generation to the specific reference text. More steps at this setup are unlikely to get us there by themselves.

Best next bet:
1. Stop blind longer continuation from this configuration.
2. Build an eval set that directly measures reference-specific style transfer with harder own-vs-swap prompts.
3. Clean/filter training pairs for instruction-answering contamination and remove outputs that explain, analyze, advertise, or mention writing tasks.
4. Try a prompt-format/data-format run where the target is always pure continuation/poem text, and eval uses the same format.
5. Consider stronger contrastive/style losses only after the data/eval format is tightened, because the current own-vs-swap signal is not reliably aligned with generation quality.
