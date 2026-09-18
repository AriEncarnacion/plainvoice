#!/usr/bin/env python3
"""Check English docs against their Chinese originals.

Pairs `<name>.md` with `<name>.zh-CN.md` and reports structural and semantic
drift. Standard library only, matching the rest of scripts/.

    python3 scripts/check_translation.py              # all pairs
    python3 scripts/check_translation.py README.md    # one pair
    python3 scripts/check_translation.py --baseline   # record current findings
    python3 scripts/check_translation.py --compare    # fail only on NEW findings
    python3 scripts/check_translation.py --selftest   # check the merge logic

`--baseline` merges, refreshing only the pairs it just checked, so a single-file
run does not discard the rest. Regenerate it whenever findings are fixed: a
baseline entry that no longer reproduces still whitelists that exact finding,
so reintroducing it would pass `--compare`. `--compare` now says when that has
happened.

HARD failures are structural and always actionable. SOFT findings need a human
to look at the line; they are expected to be non-zero even on good files.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASELINE = ROOT / "qa" / "translation-baseline.json"

# ponytail: soft checks warn instead of failing. A gate that fires on every
# file at baseline gets ignored, and then it is worse than no gate at all.

ZERO_WIDTH = re.compile(r"[​‌‍⁠﻿]")
CJK = re.compile(r"[一-鿿]")
LINK = re.compile(r"\]\(([^)\s]+)\)")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
ARTIFACTS = re.compile(r"\[(location missing|link/reference|link/documentation|then\b|\.\.\.)", re.I)
HEDGE_ZH = re.compile(r"可能|未必|大致|不一定|尚未|暂时|初步")
HEDGE_EN = re.compile(
    r"\b(may|might|could|likely|unlikely|not necessarily|preliminary|"
    r"tentative|provisional|not yet|so far|appears?|suggests?)\b", re.I)

# Scale words, so 600万 and "6 million" compare equal instead of looking
# like digit corruption. Without this the numeric check fires on most files.
ZH_SCALE = {"千": 10**3, "万": 10**4, "亿": 10**8}
EN_SCALE = {"thousand": 10**3, "million": 10**6, "billion": 10**9}
NUM_ZH = re.compile(r"(\d+(?:[,\d]*\d)?(?:\.\d+)?)\s*([千万亿])?")
# The language-selector row deliberately links to the other language.
SELECTOR = re.compile(r"简体中文|\[English\]")
NUM_EN = re.compile(r"(\d+(?:[,\d]*\d)?(?:\.\d+)?)\s*(thousand|million|billion)?", re.I)

# Terms whose wrong rendering MT actually produced in this corpus. The agents
# see MT's output first, so the negatives matter as much as the positives.
BANNED = {
    r"\bsound preservation\b": "voice preservation (声音保留)",
    r"\bproofreading\b|\bproofs\b": "provenance (keep the loanword)",
    r"\bagency\b|\bAgenda\b": "agentic",
    r"\bligatures?\b": "run-on sentences (连写句子)",
    r"\bdoes not cover\b": "does not overwrite (不覆盖)",
    r"\bmanuscripts?\b": "draft (稿/稿件)",
    r"\bpunctuation marks\b": "check: 人标句对 = human-annotated sentence pairs",
    r"\bsuggested version\b": "prompt version (提示版本)",
}
# Legitimate uses that must not be flagged.
ALLOW = re.compile(
    r"native[- ]English|non-native|version-hash isolation|isolation rules?|"
    r"quarantine|NATIVE", re.I)
CONTEXT_BANNED = {
    r"\bnative\b": "local (本机)",
    r"\bgroups?\b": "collection (分组 — the live URL parameter is `collection`)",
    r"\bisolation\b": "quarantine (隔离)",
    r"\bsignature\b": "byline (署名)",
}


def canon_nums(text, chinese):
    out = []
    pat, scales = (NUM_ZH, ZH_SCALE) if chinese else (NUM_EN, EN_SCALE)
    for m in pat.finditer(text):
        raw, scale = m.group(1).replace(",", ""), m.group(2)
        try:
            val = float(raw)
        except ValueError:
            continue
        if scale:
            val *= scales[scale.lower()] if not chinese else scales[scale]
        # 09 and 9 are the same number; leading zeros differ across languages.
        out.append(f"{val:.10g}")
    return sorted(out)


def check(en_path):
    zh_path = en_path.with_name(en_path.name[:-3] + ".zh-CN.md")
    if not zh_path.exists():
        return None
    en, zh = en_path.read_text("utf-8"), zh_path.read_text("utf-8")
    en_lines, zh_lines = en.split("\n"), zh.split("\n")
    hard, soft = [], []

    # prompts/ carry the as-run Chinese template plus an English equivalent, so
    # they are deliberately longer than their Chinese source.
    bilingual = en_path.parent.name == "prompts"
    if len(en_lines) != len(zh_lines) and not bilingual:
        hard.append(f"line count {len(en_lines)} != zh {len(zh_lines)} "
                    f"(1:1 alignment lost — findings can no longer be located by line)")

    en_body = "\n".join(l for l in en_lines if not SELECTOR.search(l))
    en_links = {t for t in LINK.findall(en_body) if not t.startswith(("http", "#", "mailto"))}
    zh_body = "\n".join(l for l in zh_lines if not SELECTOR.search(l))
    zh_links = {t.replace(".zh-CN.md", ".md") for t in LINK.findall(zh_body)
                if not t.startswith(("http", "#", "mailto"))}
    for miss in sorted(zh_links - en_links):
        hard.append(f"link target missing vs zh: {miss}")
    for extra in sorted(en_links - zh_links):
        hard.append(f"link target not in zh: {extra}")
    for i, line in enumerate(en_lines, 1):
        if ".zh-CN.md" in line and not SELECTOR.search(line):
            hard.append(f"{i}: English doc links to a Chinese sibling")
        if ZERO_WIDTH.search(line):
            hard.append(f"{i}: zero-width character")
        if ARTIFACTS.search(line):
            hard.append(f"{i}: machine-translation artifact placeholder")

    fences = [l for l in en_lines if l.lstrip().startswith("```")]
    if len(fences) % 2:
        hard.append(f"unbalanced code fences ({len(fences)})")
    for i, line in enumerate(en_lines, 1):
        if re.fullmatch(r"(bash|sh|json|python|text|js|sql|yaml)", line.strip()):
            hard.append(f"{i}: bare language tag — opening fence was destroyed")

    for i, (e, z) in enumerate(zip(en_lines, zh_lines), 1):
        if bilingual:
            break
        if z.lstrip().startswith("|") and not e.lstrip().startswith("|"):
            hard.append(f"{i}: table row lost its leading pipe")
        elif z.count("|") != e.count("|") and z.count("|") > 1:
            soft.append(f"{i}: table cell count {e.count('|')} vs zh {z.count('|')}")

    zh_ids = {m.group().lower() for m in IDENT.finditer(zh)}
    en_ids = {m.group().lower() for m in IDENT.finditer(en)}
    # `pair` in the Chinese legitimately surfaces as `pairs`/`paired`/`pairing`,
    # so match on prefix rather than exact token or the check is all noise.
    gone = sorted(t for t in zh_ids - en_ids
                  if not any(e.startswith(t) or t.startswith(e) for e in en_ids))
    if gone:
        soft.append(f"Latin identifiers in zh but not en: {', '.join(gone[:12])}")

    zn, enum = canon_nums(zh, True), canon_nums(en, False)
    if zn != enum:
        from collections import Counter
        lost = Counter(zn) - Counter(enum)
        if lost:
            soft.append(f"numbers in zh not found in en: {dict(list(lost.items())[:8])}")

    for i, line in enumerate(en_lines, 1):
        if (CJK.search(line) and "`" not in line and "*" not in line
                and not SELECTOR.search(line) and not bilingual):
            soft.append(f"{i}: Chinese outside a code span or gloss")

    for pat, want in BANNED.items():
        for i, line in enumerate(en_lines, 1):
            if re.search(pat, line, re.I):
                soft.append(f"{i}: banned rendering — use {want}")
    for pat, want in CONTEXT_BANNED.items():
        for i, line in enumerate(en_lines, 1):
            if re.search(pat, line, re.I) and not ALLOW.search(line):
                soft.append(f"{i}: check term — likely {want}")

    zh_h, en_h = len(HEDGE_ZH.findall(zh)), len(HEDGE_EN.findall(en))
    if zh_h and en_h < zh_h * 0.6:
        soft.append(f"hedge markers {en_h} vs zh {zh_h} — a dropped caveat "
                    f"turns a hypothesis into a finding")
    return hard, soft


def merge_baseline(existing, fresh):
    """Refresh only the pairs just checked; leave every other entry alone.

    A single-file run (`check_translation.py README.md --baseline`) must not
    discard the other 23 files' baselines.
    """
    out = dict(existing)
    out.update(fresh)
    return out


def selftest():
    old = {"a.md": {"hard": ["gone"], "soft": []},
           "b.md": {"hard": ["kept"], "soft": ["also kept"]}}
    new = {"a.md": {"hard": [], "soft": []}}
    m = merge_baseline(old, new)
    assert set(m) == {"a.md", "b.md"}, "a single-file run dropped other files"
    assert m["a.md"]["hard"] == [], "the checked file was not refreshed"
    assert m["b.md"]["hard"] == ["kept"], "an unchecked file's entry was lost"
    print("selftest ok")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if "--selftest" in flags:
        selftest()
        return 0
    targets = ([ROOT / a for a in args] if args else
               sorted(p for p in ROOT.rglob("*.md")
                      if not p.name.endswith(".zh-CN.md")
                      and ".git" not in p.parts and "data/local" not in str(p)))

    results, hard_total, soft_total = {}, 0, 0
    for p in targets:
        got = check(p)
        if not got:
            continue
        hard, soft = got
        rel = str(p.relative_to(ROOT))
        results[rel] = {"hard": hard, "soft": soft}
        hard_total += len(hard)
        soft_total += len(soft)
        if hard or soft:
            print(f"\n\033[1m{rel}\033[0m")
            for h in hard:
                print(f"  \033[31mHARD\033[0m {h}")
            for s in soft:
                print(f"  \033[33msoft\033[0m {s}")

    print(f"\n{len(results)} pairs | {hard_total} hard | {soft_total} soft")

    if "--baseline" in flags:
        BASELINE.parent.mkdir(exist_ok=True)
        existing = json.loads(BASELINE.read_text("utf-8")) if BASELINE.exists() else {}
        merged = merge_baseline(existing, results)
        BASELINE.write_text(json.dumps(merged, indent=1, ensure_ascii=False), "utf-8")
        print(f"baseline updated for {len(results)} of {len(merged)} pairs "
              f"in {BASELINE.relative_to(ROOT)}")
        return 0
    if "--compare" in flags and BASELINE.exists():
        base = json.loads(BASELINE.read_text("utf-8"))
        new = stale = 0
        for rel, r in results.items():
            was = set(base.get(rel, {}).get("hard", []) + base.get(rel, {}).get("soft", []))
            now = set(r["hard"] + r["soft"])
            for f in sorted(now - was):
                print(f"\033[31mNEW\033[0m {rel}: {f}")
                new += 1
            stale += len(was - now)
        print(f"{new} new findings vs baseline")
        # A baseline entry that no longer reproduces still whitelists that exact
        # finding, so reintroducing it would pass the gate. Say so out loud.
        if stale:
            print(f"\033[33mnote\033[0m  baseline lists {stale} finding(s) that no longer "
                  f"reproduce and are therefore whitelisted; rerun --baseline")
        return 1 if new else 0
    return 1 if hard_total else 0


if __name__ == "__main__":
    sys.exit(main())
