#!/usr/bin/env python3
"""Generate GitHub-style contribution calendar SVGs (dark + light).

Fetches the last year of contributions for USERNAME from the public
github-contributions-api and renders assets/contributions-{dark,light}.svg
using GitHub's exact palette and layout (weeks as columns, Sunday first).
"""

import datetime
import json
import urllib.request
from pathlib import Path

USERNAME = "freezer71"
API = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"

THEMES = {
    "dark": {
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "text": "#8b949e",
        "background": "#0d1117",
    },
    "light": {
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "text": "#656d76",
        "background": "#ffffff",
    },
}

CELL = 11
GAP = 3
PITCH = CELL + GAP
LEFT = 32
TOP = 20
FONT = "font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif' font-size='12'"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_days():
    with urllib.request.urlopen(API, timeout=30) as resp:
        data = json.load(resp)
    days = sorted(data["contributions"], key=lambda d: d["date"])
    for d in days:
        d["dt"] = datetime.date.fromisoformat(d["date"])
    return days


def build_weeks(days):
    """Group days into columns of 7, Sunday first, like GitHub."""
    weeks = []
    # pad the first week so the first day lands on its weekday row
    first_row = (days[0]["dt"].weekday() + 1) % 7  # Sunday=0
    week = [None] * first_row
    for d in days:
        week.append(d)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        weeks.append(week + [None] * (7 - len(week)))
    return weeks


def month_labels(weeks):
    """Column index -> month label at each month change, no crowding."""
    changes = []
    prev = None
    for i, week in enumerate(weeks):
        first = next((d for d in week if d), None)
        if not first:
            continue
        m = first["dt"].month
        if m != prev:
            changes.append((i, MONTHS[m - 1]))
            prev = m
    # drop a label if the next one is fewer than 3 columns away
    return [(i, label) for k, (i, label) in enumerate(changes)
            if k + 1 >= len(changes) or changes[k + 1][0] - i >= 3]


def render(weeks, theme):
    colors = THEMES[theme]
    width = LEFT + len(weeks) * PITCH + 8
    height = TOP + 7 * PITCH + 30
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' "
        f"height='{height}' viewBox='0 0 {width} {height}'>"
    ]
    for i, label in month_labels(weeks):
        x = LEFT + i * PITCH
        parts.append(f"<text x='{x}' y='{TOP - 7}' fill='{colors['text']}' {FONT}>{label}</text>")
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = TOP + row * PITCH + CELL - 2
        parts.append(f"<text x='0' y='{y}' fill='{colors['text']}' {FONT}>{label}</text>")
    for col, week in enumerate(weeks):
        for row, d in enumerate(week):
            if d is None:
                continue
            x = LEFT + col * PITCH
            y = TOP + row * PITCH
            fill = colors["levels"][d["level"]]
            parts.append(
                f"<rect x='{x}' y='{y}' width='{CELL}' height='{CELL}' "
                f"rx='2' ry='2' fill='{fill}'><title>{d['count']} contributions "
                f"on {d['date']}</title></rect>"
            )
    legend_y = TOP + 7 * PITCH + 8
    legend_x = width - 8 - 5 * PITCH - 66
    parts.append(f"<text x='{legend_x - 34}' y='{legend_y + CELL - 2}' fill='{colors['text']}' {FONT}>Less</text>")
    for lvl in range(5):
        x = legend_x + lvl * PITCH
        parts.append(
            f"<rect x='{x}' y='{legend_y}' width='{CELL}' height='{CELL}' "
            f"rx='2' ry='2' fill='{colors['levels'][lvl]}'/>"
        )
    parts.append(f"<text x='{legend_x + 5 * PITCH + 4}' y='{legend_y + CELL - 2}' fill='{colors['text']}' {FONT}>More</text>")
    parts.append("</svg>")
    return "".join(parts)


def main():
    days = fetch_days()
    weeks = build_weeks(days)
    out_dir = Path(__file__).resolve().parent.parent / "assets"
    out_dir.mkdir(exist_ok=True)
    for theme in THEMES:
        svg = render(weeks, theme)
        (out_dir / f"contributions-{theme}.svg").write_text(svg)
        print(f"assets/contributions-{theme}.svg written ({len(weeks)} weeks)")


if __name__ == "__main__":
    main()
