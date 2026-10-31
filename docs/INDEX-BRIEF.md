# Indexing brief: Bell Syndicate crosswords

You are indexing newspaper page images for a crossword research project. Each image is a full
newspaper page from 1924-25 (Newspapers.com download), named paper_yyyy_mm_dd_page.jpg. Each
page should contain a crossword, usually headed "Cross Word Puzzle", that may be the Bell
Syndicate's.

RULE: index only. Do NOT transcribe clue lists or answers. Read only the fields below.

For each image, make a downsampled copy to find the puzzle, then crop the grid, heading and any
copyright line at full resolution. For each crossword on the page, record:

- number_printed: a series number, as in "Puzzle No. 12". Empty if none; say so in notes if you
  looked hard. Don't count the numbers in the grid.
- heading: the exact heading above the puzzle.
- credit: any constructor credit, verbatim; empty if none.
- copyright_line: any copyright or syndicate line near the puzzle, verbatim, including misprints.
  Printers slipped: "The Ball Syndicate" and a copyright of 1921 both occur.
- attribution: `printed` only if the line belongs to the puzzle: it sits with the heading, the
  intro, the grid or the solution. A Bell line ending a story, column or cartoon on the same page
  is not attribution; put it in notes and use `unknown`.
- shape: square or other, and squares across and down if easy to see.
- fingerprint: the first clue only, with its number, as a matching key.
- solution_label: the label on any printed solution, verbatim, as in "Solution of Last Week's
  Puzzle". Note if the page says when the next solution appears.
- continuity: does the solution on this page answer the previous found page's puzzle? yes, no,
  none printed or unclear, with the evidence.
- notes: an intro, an announcement of a new series or a changed day, a "How to Solve" box.
