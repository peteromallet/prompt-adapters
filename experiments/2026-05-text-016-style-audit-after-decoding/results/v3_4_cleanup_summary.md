# v3.4 Artifact Cleanup Summary

Status: candidate corpus built and gated.

## Approach

Four cheap subagents audited the cleanup surface independently:

- poetry artifacts;
- screenplay artifacts;
- speech artifacts;
- pipeline/gating architecture.

The consolidation rule was deterministic-first:

1. strip safe line-level artifacts;
2. blocklist only high-confidence poisoned target docs;
3. clean the full pool;
4. re-split by author after cleaning;
5. reject the corpus unless every active register still clears heldout gates.

## Implemented

Builder updates:

- poetry line cleanup for note/page labels, picture captions, performance cue
  lines, and standalone `CONTINUED.`;
- screenplay line cleanup for bare page-number and standalone continuation
  boilerplate;
- screenplay residual artifact filter for the same line classes;
- speech exact-header artifact filter for public-record openings.

Blocklist:

- `text-ip-adapter/data/audits/v3_4_artifact_blocklist.json`
- source: merged high-confidence target-doc blocklists from the poetry,
  screenplay, and speech subagent reports.

Candidate corpus:

- `text-ip-adapter/data/pairs_v3_4_artifact_clean_core3`
- SHA256 over core files:
  `cee24f455357229f7dc8699b69a1f90f8c282de1e0c62091bce30d7b4e3e9033`

## Gate Result

All data gates pass after re-splitting from the cleaned pool.

| split | poetry | screenplay | speech | heldout authors |
| --- | ---: | ---: | ---: | --- |
| train | 2,265 | 5,635 | 919 | n/a |
| val | 183 | 50 | 50 | 2/register |
| test | 147 | 50 | 50 | 2/register |

Author-disjoint gates pass for train/val/test.

Removed rows from the cleaned pool:

| register | removed |
| --- | ---: |
| poetry | 14 |
| screenplay | 24 |
| speech | 70 |

Line cleanup counts were much larger, especially screenplay page/continuation
noise, because safe line stripping preserves otherwise-good rows.

## Important Finding

Cleaning inside the old v3.3 split initially starved speech heldout coverage.
That failure is exactly why the pipeline must clean first and then re-split.
The final v3.4 candidate uses the corrected order and passes gates.

## Remaining Caveats

Residual broad scans still flag benign words such as `assignment` inside normal
screenplay dialogue. Those should not become global filters.

Some poetry rows contain roman-numeral section headings or dramatic verse
markers that are hard to distinguish from legitimate poem structure. The current
rules avoid broad deletion there and use high-confidence blocklisting instead.

## Next

Do not train solely because v3.4 exists. First finish the style audit on 015
sampled outputs. If style carryover remains weak, v3.4 is the right cleaned data
base for the next contrastive-on smoke run.
