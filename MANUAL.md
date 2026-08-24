# Manual

## What this is

A demonstration/prototype for "adaptive text": a piece of text that can be
rendered at different levels of detail, formality, and reading complexity,
under either automatic or manual user control, with a mocked
pay-per-detail-level unlock mechanism. It is not a finished product — it's a
working proof of concept plus a step-by-step build log
(`development-guide.md`) for turning it into one.

There is no text-to-speech or audio component anywhere in this repo. The
"adaptive" in the name refers to adapting the *written* text — resolution,
tone, and reading level — not to speech synthesis. See "About the espeak-ng
directory" below.

## The three control axes

Implemented identically (same value ranges, same descriptions) in both
`adaptive_text_demo.py` (mocked) and `adaptive_text_integration.py` /
`processors/text_transformer.py` (real LLM calls):

| Axis | Range | Meaning |
|---|---|---|
| Resolution | 0-3 | 0 = brief summary (~20-30% length), 1 = condensed (~40-60%), 2 = standard/full, 3 = expanded with added context |
| Formality | 1-10 | 1-3 casual/conversational, 4-6 neutral professional, 7-10 formal/academic |
| Reading age | 8-18 | Mapped to elementary / middle school / high school / college reading level |

In the real (non-mock) path, these are turned into an instruction paragraph
and sent to an LLM as part of the prompt (see
`_build_prompt` in `processors/text_transformer.py`, or the equivalent
inline code in `adaptive_text_integration.py`). The model is asked to
preserve all factual content and not add new information — there is no
verification that it actually does either; this is a prompt instruction,
not an enforced guarantee.

## How "accessibility" fits in

The accessibility angle here is *reading accessibility*: letting a reader
dial text down to a summary, or up to expanded detail, and adjust reading
level and tone to match their needs — e.g. a simpler reading age for
someone who wants faster comprehension, without changing the underlying
source article. That is the whole of the accessibility scope. There is no
screen-reader support, no audio narration, and no text-to-speech
integration in this codebase.

## The micropayment / persistence layer

Entirely mocked, and entirely local:

- A per-session **wallet** starts at 100 credits (Streamlit
  `session_state`).
- **Cost** for unlocking a block is `base_cost[resolution] + 0.1 * (|formality-5| + |reading_age-14|)`,
  with resolution 0 (summary) always free.
- **Purchases** are recorded in a local SQLite database
  (`adaptive_text_purchases.db`) keyed on `(user_id, block_id,
  resolution_level)`, with `user_id` hardcoded to `"demo_user"` — there is
  no real authentication.
- Once "purchased," a block's transformed content can be downloaded as a
  text file.

There is no real payment gateway. The README sketches a hypothetical Stripe
integration; none of that code exists in the repo.

## Two parallel implementations

The repo actually contains two independent implementations of similar
functionality that do not share code (see `DEVELOPMENT.md` for why):

1. **Flat demo scripts** — `adaptive_text_demo.py` and
   `adaptive_text_integration.py`. Each is self-contained (own SQLite
   handling, own prompt-building logic inline). These are what
   `GUIDE.md` tells you to run.
2. **Modular package** — `database/` (schema + persistence functions) and
   `processors/text_transformer.py` (a `TextTransformer` class supporting
   both OpenAI and Anthropic backends). This is the architecture sketched
   in `development-guide.md`'s phased build plan. Only `tests/test_transform.py`
   actually imports and exercises this path; the demo scripts do not use it.

## Caching

Both LLM-calling paths cache transformations in SQLite, keyed on a SHA-256
hash of the input text plus the three parameter values, so repeating a
request with the same text and settings is free and instant on the second
call. `AdaptiveTextProcessor.get_cache_stats()` in
`adaptive_text_integration.py` reports cache size and an estimated dollar
saving.

## Known gaps (as found in the repo, not aspirational)

- `tests/test_transform.py` exercises `processors/text_transformer.py`,
  which requires a real `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` at
  construction time and makes live API calls — there is no mocking, so the
  tests cannot run offline or in CI without credentials and network access.
- `pytest` is used by the tests but is not listed in `requirements.txt`.
- `tests/cache.py` is not a test (no `test_` functions, not pytest-shaped):
  it is a copy of the "warm the cache" example script from
  `development-guide.md`, and calls an undefined `get_article_blocks()` if
  run directly.
- The README states an MIT license; there is no `LICENSE` file in the repo.
- `ui/` exists as an empty directory (referenced in the phased plan in
  `development-guide.md` but never populated).

## About the espeak-ng directory

`espeak-ng/` in the working copy is **not part of this repo**: it is an
untracked, unrelated git checkout (remote `fairflow/espeak-ng-pt-br`) of a
different project of Matthew's, sitting on disk inside the same folder. It
is not a git submodule of `adaptive-text` (there is no `.gitmodules` entry),
it is not referenced by any file tracked in this repo, and it has no
functional connection to the adaptive-text/resolution-viewer code described
above. Treat it the same way as the nested `writing/` checkout: present on
disk, unrelated to this project.
