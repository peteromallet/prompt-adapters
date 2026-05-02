# Pair Style Audit v2 Worker Brief

You are auditing poetry training pairs for a style adapter.

Your job is not to preserve data volume. Your job is to decide whether each ref-target pair is a
good training example for medium-to-strong distinctive writing style.

## Input

One shard JSONL file. Each row has:

- `pair_id`
- `author`
- `author_name`
- `ref_title`, `ref_text`
- `target_title`, `target_text`

## Output

Write exactly one JSONL decision file for your shard:

`prompt-adapters/projects/poetry-clean-corpus/pair_style_audit_v2/decisions/decisions_shard_XX.jsonl`

One output row per input row, same order.

Required fields:

```json
{
  "pair_id": "...",
  "decision": "keep|delete|edit",
  "style_strength": "strong|medium|weak",
  "cleanliness": "clean|minor_issues|dirty",
  "reason": "short concrete reason",
  "ref_text": "only include for edit",
  "target_text": "only include for edit"
}
```

Use `edit` only for small trims of obvious title/footer/OCR cruft. Do not rewrite style. If fixing
would require real rewriting, use `delete`.

## Keep

Keep a pair only when both texts are clean poems and the writing style is medium or strong:

- distinctive diction, syntax, rhythm, lineation, voice, dialect, rhetorical structure, or form
- reference and target feel compatible enough to teach one author/style
- target is new content, not a near copy of the reference
- no visible prompt/instruction/metadata behavior

## Delete

Delete if any of these are true:

- bland generic poem language where many poets could have written it
- weak author/style signal, even if technically clean poetry
- prose, prose broken into lines, essay/explanation, Q&A, lesson text, or summary
- OCR damage, metadata, page headers, footers, table of contents, title lists, dedications as main content
- drama/dialogue/script-like excerpt unless the poetic voice is clearly distinctive and coherent
- ref and target feel stylistically inconsistent enough to train an unstable author representation
- too short to carry style, or too long/diffuse to be a clean style sample
- mostly copied phrasing from ref to target

## Style Strength

- `strong`: clearly recognizable voice/form/register; style is hard to confuse with generic poetry.
- `medium`: real style signal, but less unmistakable.
- `weak`: clean enough text maybe, but bland, generic, or not useful for style learning.

## Cleanliness

- `clean`: no visible artifacts.
- `minor_issues`: small removable title/footer/OCR issue, otherwise useful.
- `dirty`: artifacts or non-poetry materially affect the sample.

## Decision Policy

- `keep`: style is `medium` or `strong`, cleanliness is `clean`, and the pair is coherent.
- `edit`: style is `medium` or `strong`, cleanliness is `minor_issues`, and a small trim fixes it.
- `delete`: style is `weak`, cleanliness is `dirty`, or pair coherence is poor.

Be strict. The goal is a smaller high-quality corpus, not maximum retention.
