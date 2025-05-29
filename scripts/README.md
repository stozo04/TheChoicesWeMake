
# 📜 Scripts & Automation

This folder hosts helper scripts that automate narrative testing and other tasks for **Choices We Make**.

---

## Folder layout

```
ChoicesWeMake/
├── scripts/
│   └── verify_chapter.py      # YAML‑based narrative test runner
├── tests/
│   ├── plot/                  # chapter‑specific specs
│   └── global/                # cross‑chapter invariants
├── chapters/                  # prose
├── requirements.txt           # pyyaml, python‑dotenv, openai (optional)
└── …
```

---

## 1  Installation

```bash
# (optional) create / activate virtualenv
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

*Omit the `openai` line in `requirements.txt` if you will not run semantic checks.*

---

## 2  OpenAI key (only for semantic tests)

1. Create a **`.env`** file at repo root:

   ```text
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. `verify_chapter.py` auto‑loads `.env` via **python‑dotenv**.  
   No system‑wide env variable needed.

---

## 3  Basic usage

```bash
# run ALL tests (global + chapter) on a single file
python scripts/verify_chapter.py chapters/05_confessions_and_comfort.txt
```

Exit codes  
* `0` – all green  
* `1` – one or more tests failed  
* `2` – file or YAML missing

---

## 4  Focused rewrite loop

Skip noise from other chapters:

```bash
python scripts/verify_chapter.py        chapters/05_confessions_and_comfort.txt        --chapter-only
```

Only failures originating from that file are reported.

---

## 5  Useful flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--tests-dir` | `tests` | Point to alternate tests folder |
| `--openai-key` | env value | Override key from `.env` |
| `--chapter-only` | off | Filter failures to the target file |
| *(future)* `--skip-global` | off | Ignore `tests/global/` YAML (optional) |

---

## 6  Multi‑file verify (requires multi‑chapter argparse tweak)

```bash
python scripts/verify_chapter.py        chapters/01_coffee_shop_confessions.txt        chapters/10_shadows_of_a_stranger.txt        --chapter-only
```

---

## 7  CI integration (GitHub Actions)

```yaml
name: Narrative-Tests
on: [push, pull_request]

jobs:
  pdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          files=$(git diff --name-only ${{ github.base_ref }} -- '*.txt' | grep '^chapters/' || echo '')
          if [ -z "$files" ]; then files=$(ls chapters/*.txt); fi
          for f in $files; do
            python scripts/verify_chapter.py "$f"
          done
```

---

## 8  Extending the runner

* **New scopes** – edit `_iter_chapter_paths()`  
* **Custom assertions** – add new YAML keys (`must_count`, etc.)  
* **Lint pass** – integrate Proselint, Grammarly API, etc.  
* **Autofix** – prototype a `--autofix` flag for AI‑assisted patching

---

## 9  Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| Unicode decode error | Ensure chapter files are UTF‑8 or script reads with `encoding='utf-8'` |
| Semantic checks skipped | No `OPENAI_API_KEY` in `.env` and not supplied by flag |
| Global noise during rewrite | Add `--chapter-only` or tweak YAML `scope` |

---

Happy testing & storytelling! 🚦📚
