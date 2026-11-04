# BinairoPress

Build print-ready **Binairo (binary Sudoku) puzzle books for Amazon KDP** where every puzzle is *proven* to have exactly one completion.

## Why

Binairo has four rules — half filled / half open in every line, never three in a row, no two rows or columns alike — and freehand generators break all of them quietly: dig one given too many and a second grid completes the puzzle. BinairoPress digs with a proof in hand:

1. A completed grid is generated first by row-pattern backtracking (balanced rows, no three-in-a-row, all rows and columns distinct).
2. Givens are dug in **180°-rotationally symmetric pairs**, so every printed puzzle keeps the balanced look of the classic form.
3. Every dig is kept only while a **propagation solver** (balance forcing, pair/sandwich forcing) proves the puzzle still has **exactly one** completion — the printed solution.

## Use

**App (Windows):** launch `BinairoPress.exe`, choose the puzzle count, grid size (6×6 / 8×8 / 10×10) and a seed, click **Build the book**. Output: `binairo_book.pdf` in a `binairopress_out` folder — title page, one puzzle per page (filled and open circles), then full solutions. 8.5×11in (612×792pt).

**Command line:** `python binairo_press.py out/ --puzzles=50 --size=8 --seed=42`

A 6-puzzle sample book is included (`sample_book.pdf`).

## Verified

Acceptance test (8/8 PASS, `test/acceptance_results.txt`): a 6-puzzle 8×8 book re-verified by an independent checker that enumerates candidate rows as raw bit patterns and assembles them under column constraints (a different code path from the engine's propagation solver) — exactly one completion, equal to the printed solution; every printed solution obeys all four rules; every given matches the solution; flipping a single given breaks the proof (the tampered puzzle admits a second completion); PDF exactly 11 pages at 612×792pt; whole book in about 0.7 seconds; deterministic for a fixed seed.

## Scope

Classic Binairo / binary Sudoku on 6×6–10×10 grids — a public-domain puzzle form. 100% local — no uploads, no accounts, no per-book fees. Deterministic seeds make series production repeatable.

## Build from source

`pip install pyinstaller reportlab`, then `pyinstaller binairopress.spec`. Or push to GitHub and let the included Actions workflow build the Windows package.
