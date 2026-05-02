# Exp038 Gemma3 4B pretrained cold-start readout

Status: completed; pod terminated.

Run:
- Base: `google/gemma-3-4b-pt`
- Init: cold-start adapter
- Data: `pairs_v5_10_poetry_llm_style_medium_strong`
- Train rows: 2868
- Steps: 2400
- Checkpoints evaluated: step 800, step 1600, final
- Note: `step_2400.pt` was skipped because the trainer writes `final.pt` at the terminal step.

## Metrics

| checkpoint | K swap | V swap | z swap | adapter+prompt win / delta | own vs swap win / delta | adapter vs no-ref win / delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step 800 | 0.060 | 0.269 | 0.328 | 0.167 / -0.110 | 0.500 / -0.049 | 0.500 / -0.017 |
| step 1600 | 0.185 | 0.189 | 0.365 | 0.167 / -0.158 | 0.667 / +0.128 | 0.583 / +0.076 |
| final | 0.143 | 0.107 | 0.337 | 0.417 / +0.009 | 0.417 / -0.030 | 0.500 / +0.027 |

## Subjective read

Step 800 is bad. It has strong instruction-answering residue:
- "Haiku (5-7-5)"
- "100% guaranteed to get an A+"
- "Solution"
- notes/explanations about haiku
- assignment-style instructions

Step 1600 is the interesting checkpoint. It is the first run/checkpoint where adapter-only own-reference beats swapped-reference with a meaningful margin. Some adapter-only samples become plausibly poem-shaped, e.g. Robert Frost / Thomas Hardy / Stothert examples.

However, step 1600 is not clean:
- Prompt + adapter loses badly to prompt-only.
- Outputs still include analysis/question residue and direct source leakage.
- Some generations copy or invoke famous poems instead of transferring style.
- The adapter-only signal seems more promising than the prompted condition.

Final/2400 degrades the key style-binding signal:
- own-vs-swap drops from `0.667 / +0.128` to `0.417 / -0.030`
- prompt+adapter recovers slightly, but samples look more contaminated than step 1600
- final has explicit residues like "The reference is", "Student's response", "In response to the instruction", and activity/explanation prose.

## Conclusion

Yes, step 1600 is working in the narrow sense: it shows credible adapter-only reference specificity. It is the strongest evidence so far that the architecture can bind a reference style when using a pretrained Gemma3 base.

No, the full setup is not solved:
- The prompt+adapter eval is still mismatched or actively harmful.
- The data still contains enough instruction/explanation residue to leak into generation.
- More steps past 1600 hurt the core own-vs-swap signal.

Best next bet:
1. Preserve step 1600 as the current best checkpoint conceptually.
2. Run the next experiment around the step-1600 regime, not longer blind training.
3. Fix eval/prompt format: adapter-only may be the fairer signal for this architecture; prompt+adapter may need a much shorter, less instruction-like generation prompt.
4. Clean/filter data harder for pure target text, removing any analysis, classroom prompt, HTML, "solution", "write", "reference is", or copied canonical poem artifacts.
5. Consider a focused 1200/1600/2000 checkpoint run after data cleanup.
