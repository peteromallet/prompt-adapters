# Learnings

Status: completed, inconclusive-to-negative.

This experiment scaled the 017 direction after a stricter v3.5 cleanup. It did
not produce a clean win.

Generation quality stayed much better than the old loop failures, but the
3000-step continuation plateaued and the n20 pathway probe showed same-register
swap collapse risk (`cos_K_last_swap=0.909`). Random/code were still separated,
so the model did not globally collapse; the issue is within-register/author
separation.

The n20 default probe builder is itself a problem: it chose mostly two authors
per register and repeated the same author pairs. The canonical balanced probe is
the right shape, so a new n21 balanced probe was persisted for future eval:
`text-ip-adapter/data/pairs_v3_5_artifact_clean_core3/probes_balanced_n21.jsonl`.

Decision: do not use the 018 final checkpoint as the next training base without
more evidence. Re-evaluate 017 final and 018 early checkpoints on balanced n21;
if early checkpoints look better, stop earlier or lower LR further. If 017 also
collapses under balanced n21, the apparent 017 win was partly probe-dependent.
