# The Bell Syndicate's crossword, 1924-25

The Bell Syndicate sold one of the first syndicated crosswords. The trade press first lists it in
October 1924, but it was in the Indianapolis Star by February. A syndicate has no paper of its
own, so its puzzles survive only as copies in the papers that bought them. This is the Every
Puzzle Project's record of which papers carried Bell's crossword in 1924 and 1925, and when.

**Status page: https://everypuzzleproject.github.io/bell/**

What the run should settle is in [RESEARCH.md](RESEARCH.md): when Bell started, whether it sold
one crossword or two, how papers took it, when it went daily and who made the puzzles.

The scope stops at July 1925, when E&P has Bell daily and Sunday. The feature ran until about
1971, and the LA Times alone carried it for 39 years. Later years can come after this is done.

## What's here

| File | What it is |
|---|---|
| `printings.tsv` | One row per crossword printing seen: paper, date, page, the number printed, heading, credit, copyright line, what ties it to Bell, first-clue key, which solution the page carries, and which puzzle it is. |
| `searches.tsv` | One row per paper and date looked at: found, no-hit, not-carried, missing-from-scans. A paper that doesn't carry the puzzle on some date is recorded, not skipped. |
| `wanted.tsv` | Specific pages worth finding, each with the question it answers. |
| `papers.tsv` | The papers, with what each one's run looks like. |
| `tools/record.py` | `new`, `add`, `search`, `want`, `rebuild`, `show`: the only way the tables change. |
| `tools/render.py` | Builds the status page from the tables; runs on every push. |

## What counts as Bell

`attribution` on a printing says what ties it to Bell:

- `printed`: a Bell line belongs to this puzzle, sitting with its heading, intro or solution.
- `match`: the same puzzle as a printed copy; `match` says how.
- `unknown`: a puzzle in a Bell paper that shows no Bell line, recorded because it may turn out
  to be Bell's.

A Bell line elsewhere on the page doesn't count. Bell also sold stories and columns, and pages
with one of those and an unrelated crossword are common.

Printings and puzzles are kept apart. Copies of one puzzle share a `puzzle_key`, and copies with
the same first clue are grouped automatically. `lag_days` is the days behind the earliest copy we
have, which is not necessarily Bell's release date. Weeks run Monday to Sunday.

## The loop

1. Find a page from the status page's list. Download it as *Entire page, JPG* into
   `../bell-scans/pages/`, keeping the name Newspapers.com gives it.
2. `python tools/record.py new` lists saved pages not yet recorded. Index each one (see
   [docs/INDEX-BRIEF.md](docs/INDEX-BRIEF.md)), then `python tools/record.py add <file> key=value ...`.
   A page seen but not saved: `add clip:<paper>:<date>`. A date with nothing:
   `python tools/record.py search <paper> <date> no-hit`.
3. `python tools/render.py`, then commit both repos, naming the dates covered.

Clues and answers are not transcribed here. Puzzle content comes from the OCR pipeline (xword-ocr
and blitz), so nothing typed by hand gets in silently.

## How you can help

If you've seen a Bell crossword in a paper not listed on the status page, or a Bell puzzle with a
number, open an issue with the paper, date and a clipping link. Please don't upload page images:
issues are public.

## Images

Page images from Newspapers.com never go in this repo. They live in the private twin
`bell-scans`. Whether they're published anywhere is a separate decision, not taken here.
What's known about Bell, with sources, is in the catalog:
[bell-mcclure.md](https://github.com/EveryPuzzleProject/catalog/blob/main/syndicates/bell-mcclure.md).
