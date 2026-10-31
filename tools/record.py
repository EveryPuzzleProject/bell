#!/usr/bin/env python3
"""Keep the record of the Bell Syndicate's crossword, 1924-25, and the papers that carried it.

Three tables, all tab-separated, all edited only through this tool:

  printings.tsv  one row per crossword printing we have seen (hand-indexed from the image)
  searches.tsv   one row per paper+date looked for: found, no-hit, not-carried, missing-from-scans
  wanted.tsv     specific pages worth finding, and why; `search` and `add` close them

  python tools/record.py new [FOLDER]         page images not yet in printings.tsv (default ../bell-scans/pages)
  python tools/record.py add FILE key=value…  add or update the printing on FILE (a second puzzle on
                                              the same page: FILE#2; a printing with no saved page:
                                              clip:<paper>:<date>). Keys: page printed_page number_printed heading
                                              credit copyright_line attribution shape fingerprint solution_label
                                              url puzzle_key match continuity notes
  python tools/record.py search PAPER DATE result=no-hit|not-carried|missing-from-scans [note=…]
  python tools/record.py want PAPER DATE why=…
  python tools/record.py rebuild              weeks, puzzle groups, lags, searches 'found', the scans repo's pages.tsv
  python tools/record.py show DATE|FILE

attribution says what ties a printing to Bell: `printed` (a Bell line belongs to this puzzle),
`match` (same puzzle as a printed copy; say how in match=) or `unknown`. A Bell line elsewhere
on the page is not attribution; see docs/INDEX-BRIEF.md.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANS = ROOT.parent / "bell-scans"
PAGES = SCANS / "pages"
PAGES_TSV = SCANS / "pages.tsv"
PRINTING_COLS = ["file", "paper", "date", "weekday", "week", "page", "printed_page", "number_printed", "heading", "credit",
                 "copyright_line", "attribution", "shape", "fingerprint", "solution_label", "url", "puzzle_key",
                 "lag_days", "match", "continuity", "notes"]
SEARCH_COLS = ["paper", "date", "result", "note"]
WANTED_COLS = ["paper", "date", "why", "status"]
RESULTS = ["no-hit", "not-carried", "missing-from-scans"]
ATTRIBUTIONS = ["printed", "match", "unknown", ""]
FILE_RE = re.compile(r"^(?P<paper>.+?)_(?P<y>\d{4})_(?P<m>\d{2})_(?P<d>\d{2})_(?:Page_)?(?P<page>[A-Za-z]?\d+)(?: \(\d+\))?\.(?:jpe?g|png|pdf)$", re.I)


def week_of(date: str) -> str:
    """The Monday of a date's week. Monday-Sunday, so that a Thursday and the next Sunday, the
    gap seen between Burlington and Indianapolis, fall in one week."""
    d = dt.date.fromisoformat(date)
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def paper_id(token: str) -> str:
    t = token.lower().replace("_", "-")
    return t[4:] if t.startswith("the-") else t


def parse_file(name: str):
    m = FILE_RE.match(name)
    if not m:
        return None
    return {"paper": paper_id(m.group("paper")), "date": dt.date(int(m.group("y")), int(m.group("m")), int(m.group("d"))).isoformat(),
            "page": m.group("page")}


def read_tsv(path: Path, cols: list[str]) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t") if lines else cols
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        r = {c: "" for c in cols}
        r.update({h: v for h, v in zip(head, line.split("\t"))})
        rows.append(r)
    return rows


def write_tsv(path: Path, cols: list[str], rows: list[dict]) -> None:
    lines = ["\t".join(cols)] + ["\t".join((r.get(c) or "").replace("\t", " ").replace("\n", " ") for c in cols) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def printings() -> list[dict]:
    return read_tsv(ROOT / "printings.tsv", PRINTING_COLS)


def searches() -> list[dict]:
    return read_tsv(ROOT / "searches.tsv", SEARCH_COLS)


def wanted() -> list[dict]:
    return read_tsv(ROOT / "wanted.tsv", WANTED_COLS)


def new(args) -> None:
    known = {r["file"].split("#")[0] for r in printings()}
    n = 0
    for p in sorted(Path(args.folder).iterdir()):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".pdf"):
            continue
        info = parse_file(p.name)
        if not info:
            print(f"?? {p.name}: name not in paper_yyyy_mm_dd_page form")
        elif p.name not in known:
            n += 1
            print(f"{p.name}\t{info['paper']}\t{info['date']}\tp.{info['page']}")
    if not n:
        print("nothing new")


def add(args) -> None:
    rows = printings()
    key = args.file
    base = key.split("#")[0]
    if key.startswith("clip:"):  # a printing with no saved page: clip:<paper>:<date>
        _, paper, date = key.split(":")
        info = {"paper": paper, "date": date, "page": ""}
    else:
        info = parse_file(Path(base).name)
    if not info:
        sys.exit(f"{base}: name not in paper_yyyy_mm_dd_page form (or clip:<paper>:<date>)")
    row = next((r for r in rows if r["file"] == key), None)
    if row is None:
        row = {c: "" for c in PRINTING_COLS}
        row.update(file=key, paper=info["paper"], date=info["date"], page=info["page"])
        rows.append(row)
    settable = set(PRINTING_COLS) - {"file", "date", "weekday", "week", "lag_days"}  # paper= overrides a misnamed file
    for kv in args.pairs:
        k, _, v = kv.partition("=")
        if k not in settable:
            sys.exit(f"can't set {k}; keys: {' '.join(sorted(settable))}")
        if k == "number_printed" and v and not v.isdigit():
            sys.exit("number_printed is a number (leave empty if none; say so in notes)")
        if k == "attribution" and v not in ATTRIBUTIONS:
            sys.exit(f"attribution is one of {' '.join(ATTRIBUTIONS)}")
        if k == "notes" and v.startswith("+"):
            v = (row["notes"] + "; " if row["notes"] else "") + v[1:].strip()
        row[k] = v
    if not row["url"] and (PAGES / base).exists():
        row["url"] = url_from_zone(PAGES / base)
    rebuild_all(rows, searches())
    show_printing(row)


def url_from_zone(path: Path) -> str:
    """The Newspapers.com page link from the download's Zone.Identifier stream, if present."""
    try:
        import subprocess
        out = subprocess.run(["powershell", "-NoProfile", "-Command", f"Get-Content '{path}' -Stream Zone.Identifier"],
                             capture_output=True, text=True, timeout=20).stdout
        m = re.search(r"[?&]id=(\d+)", out)
        return f"https://www.newspapers.com/image/{m.group(1)}/" if m else ""
    except Exception:
        return ""


def search(args) -> None:
    if args.result not in RESULTS:
        sys.exit(f"result must be one of {' '.join(RESULTS)} (found is set by the tool)")
    rows = searches()
    row = next((r for r in rows if r["paper"] == args.paper and r["date"] == args.date), None)
    if row is None:
        row = {c: "" for c in SEARCH_COLS}
        row.update(paper=args.paper, date=args.date)
        rows.append(row)
    row["result"] = args.result
    if args.note:
        row["note"] = args.note
    rebuild_all(printings(), rows)
    print(f"{args.paper} {args.date}: {args.result}")


def want(args) -> None:
    rows = wanted()
    rows.append({"paper": args.paper, "date": args.date, "why": args.why, "status": ""})
    write_tsv(ROOT / "wanted.tsv", WANTED_COLS, sorted(rows, key=lambda r: (r["date"], r["paper"])))
    rebuild_all(printings(), searches())


def fp_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())[:24]


def rebuild(args) -> None:
    rebuild_all(printings(), searches())
    print("rebuilt")


def rebuild_all(pr: list[dict], se: list[dict]) -> None:
    by_fp: dict[str, list[dict]] = {}
    for r in pr:
        r["weekday"] = dt.date.fromisoformat(r["date"]).strftime("%a")
        r["week"] = week_of(r["date"])
        if r["fingerprint"]:
            by_fp.setdefault(fp_key(r["fingerprint"]), []).append(r)
    for key, copies in by_fp.items():  # copies with one first clue are one puzzle
        if len(copies) > 1:
            shared = next((c["puzzle_key"] for c in copies if c["puzzle_key"]), f"fp-{key}")
            for c in copies:
                c["puzzle_key"] = shared
    first: dict[str, str] = {}
    for r in pr:
        if r["puzzle_key"]:
            first[r["puzzle_key"]] = min(first.get(r["puzzle_key"], r["date"]), r["date"])
    for r in pr:  # days behind the earliest copy we have, not behind Bell's release
        r["lag_days"] = str((dt.date.fromisoformat(r["date"]) - dt.date.fromisoformat(first[r["puzzle_key"]])).days) if r["puzzle_key"] else ""
    pr.sort(key=lambda r: (r["date"], r["paper"], r["file"]))
    write_tsv(ROOT / "printings.tsv", PRINTING_COLS, pr)
    have = {(r["paper"], r["date"]) for r in pr}
    for s in se:
        if (s["paper"], s["date"]) in have:
            s["result"] = "found"
    for r in pr:
        if not any(s["paper"] == r["paper"] and s["date"] == r["date"] for s in se):
            se.append({"paper": r["paper"], "date": r["date"], "result": "found", "note": ""})
    se.sort(key=lambda s: (s["date"], s["paper"]))
    write_tsv(ROOT / "searches.tsv", SEARCH_COLS, se)
    closed = {(s["paper"], s["date"]): s["result"] for s in se}
    wa = wanted()
    for w in wa:
        w["status"] = closed.get((w["paper"], w["date"]), "")
    write_tsv(ROOT / "wanted.tsv", WANTED_COLS, wa)
    sync_pages_tsv(pr)


def sync_pages_tsv(pr: list[dict]) -> None:
    """The scans repo's pages.tsv (xword-ocr folder-source format): one row per image we have."""
    if not SCANS.exists():
        return
    cols = ["file", "issue", "date", "page", "url", "captured", "note"]
    old = {r["file"]: r for r in read_tsv(PAGES_TSV, cols)}
    rows = []
    seen = set()
    for r in pr:
        base = r["file"].split("#")[0]
        if base in seen or not (PAGES / base).exists():
            continue
        seen.add(base)
        o = old.get(f"pages/{base}", {})
        rows.append({"file": f"pages/{base}", "issue": f"{r['paper']}-{r['date']}", "date": r["date"], "page": r["page"],
                     "url": r["url"] or o.get("url", ""), "captured": o.get("captured") or dt.date.today().isoformat(),
                     "note": o.get("note", "") or (f"printed {r['printed_page']}" if r["printed_page"] else "")})
    write_tsv(PAGES_TSV, cols, rows)


def show_printing(r: dict) -> None:
    for c in PRINTING_COLS:
        if r[c]:
            print(f"{c:16} {r[c]}")


def show(args) -> None:
    for r in printings():
        if r["file"].startswith(args.key) or r["date"] == args.key:
            show_printing(r)
            print("--")
    for s in searches():
        if s["date"] == args.key and s["result"] != "found":
            print(f"search {s['paper']} {s['date']}: {s['result']} {s['note']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("folder", nargs="?", default=str(PAGES)); p.set_defaults(fn=new)
    p = sub.add_parser("add"); p.add_argument("file"); p.add_argument("pairs", nargs="*"); p.set_defaults(fn=add)
    p = sub.add_parser("search"); p.add_argument("paper"); p.add_argument("date"); p.add_argument("result"); p.add_argument("note", nargs="?", default="")
    p.set_defaults(fn=search)
    p = sub.add_parser("want"); p.add_argument("paper"); p.add_argument("date"); p.add_argument("why"); p.set_defaults(fn=want)
    sub.add_parser("rebuild").set_defaults(fn=rebuild)
    p = sub.add_parser("show"); p.add_argument("key"); p.set_defaults(fn=show)
    args = ap.parse_args()
    if args.cmd == "search":
        args.result = args.result.split("=")[-1]
        args.note = args.note.split("=", 1)[-1] if args.note else ""
    if args.cmd == "want":
        args.why = args.why.split("=", 1)[-1]
    args.fn(args)


if __name__ == "__main__":
    main()
