#!/usr/bin/env python3
"""BinairoPress acceptance test.

Proof-output method: build a real book (8x8, 6 puzzles), then re-verify
every puzzle with a checker written independently of the engine: it
enumerates candidate rows as raw 2^n bit patterns filtered by the
balance/no-three rules (the engine builds patterns recursively and
solves by cell propagation), then depth-first assembles rows under
column constraints and the row/column distinctness rules. Exactly one
completion may exist, equal to the printed solution. Also audits the
solution against every printed rule, givens consistency, a tamper
case (flip one given: the proof must break), PDF geometry, timing,
determinism.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from binairo_press import run_binairopress  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "out")
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def bit_patterns(n):
    pats = []
    for bits in range(2 ** n):
        row = tuple((bits >> (n - 1 - i)) & 1 for i in range(n))
        if sum(row) != n // 2:
            continue
        if any(row[i] == row[i + 1] == row[i + 2] for i in range(n - 2)):
            continue
        pats.append(row)
    return pats


def count_by_rows(givens, n, limit=2):
    """Independent recount: assemble whole rows from bit patterns."""
    pats = bit_patterns(n)
    by_row = []
    for r in range(n):
        lst = [p for p in pats
               if all(givens[r][c] in (-1, p[c]) for c in range(n))]
        if not lst:
            return []
        by_row.append(lst)
    sols = []
    grid = []

    def col_ok(c, upto):
        col = [grid[r][c] for r in range(upto)]
        if sum(col) > n // 2 or (len(col) - sum(col)) > n // 2:
            return False
        if len(col) >= 3 and col[-1] == col[-2] == col[-3]:
            return False
        return True

    def rec(r):
        if len(sols) >= limit:
            return
        if r == n:
            cols = [tuple(grid[rr][c] for rr in range(n)) for c in range(n)]
            if len(set(cols)) != n:
                return
            if any(sum(col) != n // 2 for col in cols):
                return
            if any(col[i] == col[i + 1] == col[i + 2]
                   for col in cols for i in range(n - 2)):
                return
            sols.append([list(row) for row in grid])
            return
        for p in by_row[r]:
            if p in grid:
                continue
            grid.append(p)
            if all(col_ok(c, r + 1) for c in range(n)):
                rec(r + 1)
            grid.pop()
            if len(sols) >= limit:
                return

    rec(0)
    return sols


def solution_rules_ok(sol, n):
    for r in range(n):
        if sum(sol[r]) != n // 2:
            return False
        if any(sol[r][i] == sol[r][i + 1] == sol[r][i + 2]
               for i in range(n - 2)):
            return False
    for c in range(n):
        col = [sol[r][c] for r in range(n)]
        if sum(col) != n // 2:
            return False
        if any(col[i] == col[i + 1] == col[i + 2] for i in range(n - 2)):
            return False
    if len({tuple(r) for r in sol}) != n:
        return False
    if len({tuple(sol[r][c] for r in range(n)) for c in range(n)}) != n:
        return False
    return True


def main():
    t0 = time.time()
    s = run_binairopress(6, OUT, seed=42, size=8)
    dt = time.time() - t0
    ps = s["puzzles"]
    check("counts: 6 puzzles at 8x8", len(ps) == 6 and all(p["n"] == 8 for p in ps),
          f"(givens: {[p['given_count'] for p in ps]})")

    rules_ok, giv_ok, unique_ok = True, True, True
    for p in ps:
        if not solution_rules_ok(p["solution"], p["n"]):
            rules_ok = False
        for r in range(p["n"]):
            for c in range(p["n"]):
                if p["givens"][r][c] != -1 and \
                        p["givens"][r][c] != p["solution"][r][c]:
                    giv_ok = False
        sols = count_by_rows(p["givens"], p["n"], limit=2)
        if len(sols) != 1 or sols[0] != p["solution"]:
            unique_ok = False
    check("every printed solution obeys all four Binairo rules", rules_ok, "")
    check("every given matches the printed solution", giv_ok, "")
    check("every puzzle: exactly one completion (independent bit-pattern "
          "row recount), equal to printed solution", unique_ok, "")

    # tamper: flip one given
    p0 = ps[0]
    bad = [row[:] for row in p0["givens"]]
    done = False
    for r in range(p0["n"]):
        for c in range(p0["n"]):
            if bad[r][c] != -1 and not done:
                bad[r][c] = 1 - bad[r][c]
                done = True
    sols = count_by_rows(bad, p0["n"], limit=2)
    check("tamper: one flipped given breaks the proof",
          not (len(sols) == 1 and sols[0] == p0["solution"]),
          f"(tampered count: {len(sols)})")

    with open(s["pdf_path"], "rb") as fh:
        data = fh.read()
    pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    check("PDF 612x792pt, 11 pages", b"612 792" in data and pages == 11,
          f"({pages})")
    check("6-puzzle book builds in under 180s", dt < 180, f"({dt:.1f}s)")

    s2 = run_binairopress(6, OUT, seed=42, size=8)
    same = [p["givens"] for p in s2["puzzles"]] == [p["givens"] for p in ps]
    check("deterministic for fixed seed", same, "")

    npass = sum(1 for _, ok, _ in results if ok)
    print(f"\n{npass}/{len(results)} PASS")
    with open(os.path.join(os.path.dirname(__file__),
                           "acceptance_results.txt"), "w") as fh:
        for name, ok, detail in results:
            fh.write(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}\n")
        fh.write(f"\n{npass}/{len(results)} PASS\n")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
