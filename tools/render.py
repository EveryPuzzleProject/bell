#!/usr/bin/env python3
"""Render site/index.html from printings.tsv, searches.tsv, wanted.tsv and papers.tsv.

    python tools/render.py        # then open site/index.html

Runs in CI on every push. It draws only what the tables record; weeks, groups and lags are
computed by tools/record.py rebuild, not here.
"""
import collections
import datetime as dt
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/EveryPuzzleProject/bell"
CATALOG = "https://github.com/EveryPuzzleProject/catalog/blob/main/syndicates/bell-mcclure.md"
# Newspapers.com search for one date. If this link form stops working, change it here only.
SEARCH = "https://www.newspapers.com/search/results/?date={date}&keyword=%22cross%20word%22"
FIRST_WEEK = dt.date(1923, 12, 31)   # the Monday of the first week drawn
LAST_WEEK = dt.date(1925, 7, 27)     # E&P has Bell daily and Sunday by July 1925
ATTR = {"printed": "Bell line on the puzzle", "match": "same puzzle as a Bell copy", "unknown": "not known to be Bell"}
RESULT_CLASS = {"no-hit": "nh", "not-carried": "nc", "missing-from-scans": "nc"}


def read(name: str) -> list[dict]:
    p = ROOT / name
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t")
    return [dict(zip(head, (l.split("\t") + [""] * len(head))[:len(head)])) for l in lines[1:] if l.strip()]


def e(s) -> str:
    return html.escape(s or "")


def link(url: str, text: str) -> str:
    return f'<a href="{e(url)}">{e(text)}</a>' if url else e(text)


def weekday(date: str) -> str:
    return dt.date.fromisoformat(date).strftime("%a")


def main() -> None:
    printings = read("printings.tsv")
    searches = read("searches.tsv")
    wanted = read("wanted.tsv")
    papers = {p["id"]: p for p in read("papers.tsv")}

    def pname(pid: str) -> str:
        return papers.get(pid, {}).get("name", pid)

    def date_links(paper: str, date: str) -> str:
        y, m, d = date.split("-")
        tpl = papers.get(paper, {}).get("search", "")
        return link(tpl.format(date=date, y=y, m=m, d=d) if tpl else SEARCH.format(date=date), "search that date")

    bell = [r for r in printings if r["attribution"] in ("printed", "match")]
    bell_papers = {r["paper"] for r in bell}
    earliest = min(bell, key=lambda r: r["date"]) if bell else None
    groups = collections.defaultdict(list)
    for r in printings:
        if r["puzzle_key"]:
            groups[r["puzzle_key"]].append(r)
    shared = {k: v for k, v in groups.items() if len({r["paper"] for r in v}) > 1}

    def wanted_html() -> str:
        rows = [w for w in wanted if not w["status"]]
        if not rows:
            return "<p>Nothing specific is wanted just now.</p>"
        return '<div class="scroll"><table><thead><tr><th>Date</th><th>Paper</th><th>Why</th><th>Newspapers.com</th></tr></thead><tbody>' + "\n".join(
            f"<tr><td>{e(w['date'])} {weekday(w['date'])}</td><td>{e(pname(w['paper']))}</td><td>{e(w['why'])}</td><td>{date_links(w['paper'], w['date'])}</td></tr>"
            for w in rows) + "</tbody></table></div>"

    def grid_html() -> str:
        weeks = []
        w = FIRST_WEEK
        while w <= LAST_WEEK:
            weeks.append(w)
            w += dt.timedelta(weeks=1)
        seen = collections.defaultdict(dict)
        for s in searches:
            seen[s["paper"]][(dt.date.fromisoformat(s["date"]) - dt.timedelta(days=dt.date.fromisoformat(s["date"]).weekday()))] = s
        by_week = collections.defaultdict(dict)
        for r in printings:
            by_week[r["paper"]][dt.date.fromisoformat(r["week"])] = r
        order = sorted({r["paper"] for r in printings} | set(seen), key=lambda p: min(r["date"] for r in printings if r["paper"] == p) if any(r["paper"] == p for r in printings) else "9")
        months = '<div class=cr><span class=cl></span>' + "".join(
            f'<span class="c mo">{"JFMAMJJASOND"[w.month - 1]}</span>' if (w.day <= 7) else '<span class="c mo"></span>' for w in weeks) + "</div>"
        rows = []
        for pid in order:
            cells = []
            for w in weeks:
                r = by_week[pid].get(w)
                s = seen[pid].get(w)
                if r:
                    cls = "have" if r["attribution"] in ("printed", "match") else "unk"
                    tip = f"{r['date']} {r['weekday']}, {ATTR.get(r['attribution'], '')}" + (f", No. {r['number_printed']}" if r["number_printed"] else "")
                    cells.append(f'<span class="c {cls}" title="{e(tip)}"></span>')
                elif s:
                    cells.append(f'<span class="c {RESULT_CLASS.get(s["result"], "none")}" title="{e(s["date"] + " " + s["result"])}"></span>')
                else:
                    cells.append('<span class="c none"></span>')
            rows.append(f'<div class=cr><span class=cl title="{e(pname(pid))}">{e(pname(pid))}</span>{"".join(cells)}</div>')
        return f'<div class=cg>{months}{"".join(rows)}</div>'

    def shared_html() -> str:
        if not shared:
            return "<p>No puzzle matched across papers yet.</p>"
        rows = []
        for key, copies in sorted(shared.items(), key=lambda kv: min(r["date"] for r in kv[1])):
            copies = sorted(copies, key=lambda r: r["date"])
            rows.append("<li>" + " = ".join(f"{e(pname(r['paper']))} {e(r['date'])} {e(r['weekday'])}" for r in copies) + f' <span class=muted>({e(copies[0]["match"] or copies[-1]["match"])})</span></li>')
        return f'<ul>{"".join(rows)}</ul>'

    def printings_html() -> str:
        body = "\n".join(
            f"<tr><td>{e(r['date'])}</td><td>{e(r['weekday'])}</td><td>{e(pname(r['paper']))}</td><td>{link(r['url'], r['page'] or '')}</td>"
            f"<td>{e(r['number_printed'])}</td><td>{e(r['heading'])}</td><td>{e(r['copyright_line'])}</td><td>{e(ATTR.get(r['attribution'], ''))}</td>"
            f"<td class=muted>{e(r['notes'])}</td></tr>" for r in printings)
        return ('<div class="scroll"><table id=pr><thead><tr><th>Date</th><th>Day</th><th>Paper</th><th>Page</th><th>No.</th><th>Heading</th>'
                f"<th>Copyright line</th><th>Tie to Bell</th><th>Notes</th></tr></thead><tbody>{body}</tbody></table></div>")

    page = f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1">
<title>Bell Syndicate crosswords</title>
<style>
:root {{ --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a65; --line:#e3e0d8; --card:#ffffff; --accent:#1c4f8a; --warn:#a33a1c; --s-have:#2f6f4f; --s-unk:#c29a3a; --s-wanted:#d9d5cc; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#161614; --fg:#ecebe6; --muted:#a3a19a; --line:#34332f; --card:#1f1f1c; --accent:#7aaee0; --warn:#e0794f; --s-have:#5fae86; --s-unk:#d6b35c; --s-wanted:#3b3a36; }} }}
:root[data-theme="dark"] {{ --bg:#161614; --fg:#ecebe6; --muted:#a3a19a; --line:#34332f; --card:#1f1f1c; --accent:#7aaee0; --warn:#e0794f; --s-have:#5fae86; --s-unk:#d6b35c; --s-wanted:#3b3a36; }}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 Georgia, "Times New Roman", serif }}
main {{ max-width:1100px; margin:0 auto; padding:32px 16px 64px }}
h1 {{ font-size:2rem; margin:0 0 4px }} h2 {{ margin:40px 0 8px; font-size:1.35rem; border-bottom:2px solid var(--fg); padding-bottom:4px }}
a {{ color:var(--accent) }} .muted {{ color:var(--muted) }} .lede {{ font-size:1.1rem }} code {{ font-size:0.9em }}
table {{ width:100%; border-collapse:collapse; font:14px/1.4 system-ui, sans-serif }}
th, td {{ text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top }}
th {{ font-weight:600 }} .scroll {{ overflow-x:auto }} td:first-child {{ white-space:nowrap }}
.cg {{ font:11px system-ui, sans-serif; overflow-x:auto; margin:4px 0 8px }} .cr {{ display:flex; align-items:center; gap:2px; margin:2px 0 }}
.cl {{ width:13em; flex:none; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis }}
.c {{ width:9px; height:13px; flex:none; border-radius:2px; display:inline-block }}
.c.have {{ background:var(--s-have) }} .c.unk {{ background:var(--s-unk) }} .c.nc {{ background:var(--line); border:1px solid var(--muted) }}
.c.nh {{ background:color-mix(in srgb, var(--warn) 45%, var(--bg)) }} .c.none {{ background:var(--s-wanted); opacity:.45 }}
.c.mo {{ background:none; color:var(--muted); font-size:10px; text-align:center; line-height:13px }}
.key {{ font:13px system-ui, sans-serif; color:var(--muted) }} .key .c {{ vertical-align:-2px; margin:0 3px 0 10px }}
footer {{ margin-top:48px; font:13px system-ui, sans-serif; color:var(--muted) }}
</style></head><body><main>
<h1>The Bell Syndicate's crossword</h1>
<p class=lede>Bell sold one of the first syndicated crosswords, months before the trade press listed it. This is the Every Puzzle Project's record of which papers carried it in 1924 and 1925, and when. Copies in other papers are the only way to see it, because a syndicate has no paper of its own.</p>
<p><b>{len(printings)}</b> printings recorded, <b>{len(bell)}</b> tied to Bell, in <b>{len(bell_papers)}</b> papers. Earliest so far: {e(pname(earliest['paper'])) if earliest else 'none'} {e(earliest['date']) if earliest else ''}. E&amp;P's first listing is October 1924.</p>
<h2>Pages wanted</h2>
<p>Specific pages that would settle something. Open questions are in <a href="{REPO}/blob/main/RESEARCH.md">RESEARCH.md</a>.</p>
{wanted_html()}
<h2>Which papers, which weeks</h2>
<p class=key>One square per week, Monday to Sunday, January 1924 to July 1925. Hover for the date.<span class="c have"></span>Bell<span class="c unk"></span>puzzle not known to be Bell<span class="c nh"></span>no hit<span class="c nc"></span>not carried or missing</p>
{grid_html()}
<h2>Same puzzle, different papers</h2>
{shared_html()}
<h2>Every printing</h2>
{printings_html()}
<footer><a href="{REPO}">Repository</a> · <a href="{CATALOG}">Catalog entry</a> · built {dt.date.today().isoformat()}</footer>
</main></body></html>
"""
    (ROOT / "site").mkdir(exist_ok=True)
    (ROOT / "site" / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
