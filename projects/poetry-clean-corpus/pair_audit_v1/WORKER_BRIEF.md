# Pair audit v1 worker brief

You are auditing source-native poetry training pairs for an author-style adapter.

For each JSONL row in your assigned shard, output exactly one JSON object to your assigned decision file.

Decision schema:

```json
{
  "pair_id": "...",
  "decision": "keep" | "delete" | "edit",
  "severity": "none" | "minor" | "major",
  "reasons": ["ocr", "prose", "metadata", "style_mismatch", "weak_poem", "duplicate_like", "non_poetry", "prompt_junk", "foreign_language", "drama_or_dialogue", "other"],
  "edited_ref_text": null,
  "edited_target_text": null,
  "notes": "short reason"
}
```

Keep if both texts are real poems or clear poem excerpts, both plausibly belong to the same author/style bucket, and there is no obvious OCR, TOC, publisher ad, prose criticism, biography, prompt text, metadata, or title-list material.

Delete if either side is mostly prose, preface, notes, criticism, biography, ads, TOC/index/title list, transcriber matter, badly OCR-corrupted, generic modern prompt/instruction material, or if the pair is stylistically incoherent for the claimed same author. Stylistically incoherent means one side looks like a different genre/register/era/voice than the other in a way that would teach an unstable author representation. Be strict about this, but do not delete merely because the author writes narrative verse, dialect, religious verse, archaic verse, dramatic monologue, or varied forms.

Edit only for tiny surgical cleanup: remove isolated page numbers, headers/footers, OCR marks, or one short editorial line. Do not modernize, paraphrase, improve, or creatively rewrite. If an edit would require more than removing tiny contamination, delete instead.

Optimize for precision. Ambiguous bad rows should be deleted. Output decisions only; no commentary outside JSONL.
