# Getting Started

This repo is a prototype/demo, not a packaged product: a small Streamlit app
plus a couple of supporting scripts. There are two ways to run it, and one
static HTML mockup with no backend at all.

## 1. Static mockup (no install)

`adaptive-text-demo/index.html` is a self-contained HTML/CSS/JS page — no
build step, no server, no API calls. Open it directly in a browser:

```bash
open adaptive-text-demo/index.html
```

It shows four hardcoded text variants (about AI) at different detail levels
and switches between them either automatically (based on window width) or
via a manual slider. It's a UI proof-of-concept for the "resolution slider"
idea — the text is fixed, not generated. Useful for seeing the interaction
pattern without installing anything.

## 2. Streamlit demo (mock transformations, no API key)

This is the main working demo. It fakes the text transformations (word-count
truncation and simple string substitution) so you can try the full
resolution/formality/reading-age/micropayment workflow without an API key.

```bash
python3 -m venv venv        # or use the existing venv/ if present
source venv/bin/activate
pip install -r requirements.txt
streamlit run adaptive_text_demo.py
```

Opens at `http://localhost:8501`. It creates a local SQLite file,
`adaptive_text_purchases.db`, to persist mock purchases and a wallet balance
(starts at 100 credits) across the session. That file is gitignored.

## 3. Production integration (real LLM calls, needs an API key)

`adaptive_text_integration.py` calls the OpenAI API for real (`gpt-4o-mini`
by default) and caches results in `text_transform_cache.db` (also
gitignored) so repeated requests for the same text/parameters don't re-hit
the API.

```bash
export OPENAI_API_KEY="sk-..."
python3 adaptive_text_integration.py
```

This is a script, not a web UI — read the bottom of the file (or
`AdaptiveTextProcessor` in `adaptive_text_integration.py`) to see what it
runs by default, and adapt it if you want to feed it your own text.

## What you're controlling

Three independent parameters, applied to a block of text:

- **Resolution (0-3)**: how much detail — summary, condensed, standard
  (full), or expanded.
- **Formality (1-10)**: register — casual through formal/academic.
- **Reading age (8-18)**: vocabulary/sentence complexity, roughly mapped to
  UK/US school grade bands.

In the Streamlit demo, unlocking a block at a given resolution costs mock
credits (free at resolution 0, rising with detail level and with how far
formality/reading-age are set from the middle). Purchases and the wallet
balance persist in the SQLite file.

## Troubleshooting

- **"Module not found"**: `pip install -r requirements.txt` (this installs
  Streamlit, OpenAI/Anthropic SDKs, pandas, etc. — a fairly heavy set for
  what the demo does).
- **"API key not found"**: only relevant to
  `adaptive_text_integration.py` — the Streamlit demo needs no key.
- **Database locked**: the code already opens SQLite connections with
  `check_same_thread=False`, which is the usual fix for this under
  Streamlit.

See `MANUAL.md` for what the system actually does and how the pieces fit
together, and `DEVELOPMENT.md` if you want to change the code.
