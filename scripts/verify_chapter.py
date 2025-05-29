#!/usr/bin/env python3
"""verify_chapter.py — Run YAML story tests against a single chapter (plus global invariants).

Usage:
    python verify_chapter.py chapters/01_coffee_shop_confessions.txt \
        --tests-dir tests \
        --openai-key sk-...

Exit 0 when all tests pass, 1 otherwise.
"""
from __future__ import annotations
import argparse, pathlib, sys, re, yaml, os
from dotenv import load_dotenv
load_dotenv()

try:
    import openai
except ImportError:
    openai = None

# ---------------- regex helpers ----------------
def _regex_ok(text: str, pattern: str, must: bool = True) -> bool:
    found = bool(re.search(pattern, text, flags=re.MULTILINE))
    return found if must else not found

def _semantic_ok(text: str, prompt: str, threshold: float, api_key: str | None) -> bool:
    if not api_key:
        print('[WARN] Skipping semantic check — no OpenAI key provided.')
        return True
    if openai is None:
        raise RuntimeError('openai package missing (pip install openai)')
    openai.api_key = api_key
    rsp = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role':'system','content':'Return only a float 0‑1 for how well TEXT satisfies PROMPT.'},
            {'role':'user','content':f'{prompt}\n---\n{text[:4000]}'}
        ],
        max_tokens=10
    )
    try:
        score = float(rsp.choices[0].message.content.strip())
    except Exception:
        raise RuntimeError(f'Unexpected LLM output: {rsp.choices[0].message.content}')
    return score >= threshold

# ---------------- YAML test runner ----------------
def _load_tests(path: pathlib.Path):
    data = yaml.safe_load(path.read_text())
    if not data or 'tests' not in data:
        raise ValueError(f'No tests in {path}')
    return data['tests']

# ---------- replace _iter_chapter_paths ----------
def _iter_chapter_paths(scope, target_chapter: pathlib.Path, chapters_dir: pathlib.Path):
    """
    Yields Path objects that this test should check.

    scope formats supported:
        manuscript            – legacy (same as {"chapter": "*"})
        {"chapter": "*"}      – all chapters
        {"chapter": 1}        – single chapter
        {"chapter": [1,3,10]} – selected chapters
    """
    # backward-compat
    if scope == "manuscript":
        scope = {"chapter": "*"}

    if isinstance(scope, dict) and "chapter" in scope:
        chap_spec = scope["chapter"]

        # 1) star  → every chapter file
        if chap_spec == "*":
            yield from chapters_dir.glob("*.txt")

        # 2) single int  → that chapter only
        elif isinstance(chap_spec, int):
            pattern = f"{chap_spec:02}_*.txt"
            yield from chapters_dir.glob(pattern)

        # 3) list of ints
        elif isinstance(chap_spec, list):
            for n in chap_spec:
                pattern = f"{int(n):02}_*.txt"
                yield from chapters_dir.glob(pattern)

        else:
            raise ValueError(f"Unrecognised chapter scope: {chap_spec!r}")

    else:
        # Default: just the file we’re verifying
        yield target_chapter


def run_yaml(path: pathlib.Path, target_chapter: pathlib.Path, chapters_dir: pathlib.Path, api_key: str | None):
    fails = []
    for test in _load_tests(path):
        for ch_path in _iter_chapter_paths(test.get('scope', {}), target_chapter, chapters_dir):
            text = ch_path.read_text(encoding="utf-8", errors="replace")
            # must regex
            for pat in test.get('must', []):
                if not _regex_ok(text, pat, True):
                    fails.append((test['id'], ch_path.name, f'must `{pat}`'))
            # must_not regex
            for pat in test.get('must_not', []):
                if not _regex_ok(text, pat, False):
                    fails.append((test['id'], ch_path.name, f'must_not `{pat}`'))
            # semantic
            if 'must_semantic' in test:
                sem = test['must_semantic']
                ok = _semantic_ok(text, sem['prompt'], sem['threshold'], api_key)
                if not ok:
                    fails.append((test['id'], ch_path.name, 'semantic'))
    return fails

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('chapter', help='Chapter text file to verify')
    parser.add_argument('--tests-dir', default='tests', help='Root tests directory')
    parser.add_argument('--openai-key', default=os.getenv('OPENAI_API_KEY'), help='OpenAI key for semantic checks')
    parser.add_argument('--chapter-only', action='store_true', help='Ignore failures that come from other chapter files'
)
    args = parser.parse_args()

    chap_path = pathlib.Path(args.chapter)
    if not chap_path.exists():
        print(f'Chapter file {chap_path} not found'); sys.exit(2)
    chapters_dir = chap_path.parent if chap_path.parent.name == 'chapters' else chap_path.parent.parent / 'chapters'
    tests_dir = pathlib.Path(args.tests_dir)

    yaml_files = list(tests_dir.glob('global/*.yaml')) + list(tests_dir.glob(f'plot/ch{chap_path.name[:2]}_*.yaml'))
    if not yaml_files:
        print('No YAML tests found for this chapter'); sys.exit(2)

    failures = []
    for yfile in yaml_files:
        failures.extend(run_yaml(yfile, chap_path, chapters_dir, args.openai_key))

    if args.chapter_only:
        failures = [f for f in failures if f[1] == chap_path.name]

    if failures:
        print('❌ Tests failed:')
        for tid, fname, info in failures:
            print(f'  • {tid} — {fname} — {info}')
        sys.exit(1)
    print('✅ All tests passed')
    sys.exit(0)

if __name__ == '__main__':
    main()
