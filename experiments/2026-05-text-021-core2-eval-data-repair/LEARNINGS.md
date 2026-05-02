# Learnings

Status: completed.

v3.7 repairs two issues found after 020:

- screenplay train cleanup removed dense timecode rows and page/revision debris;
- probe construction now cycles unique reference documents where possible.

Repaired-probe eval says `020_final` is still the best current checkpoint, but
the old register story was too simple. On v3.7 probes, `020_final` has
`cos_K_last_swap=0.502`; poetry is `0.522`, screenplay is `0.483`. This is
pathway-positive but not author-style-proven.

The core2 eval set itself is now the bottleneck: heldout screenplay has too few
unique reference docs, and current warmstarts have trained on many authors that
would be useful for a broader heldout split. Next work should either run
dual-judge T2/T3b on repaired n20 or build a broader clean split from a less
contaminated restart point.
