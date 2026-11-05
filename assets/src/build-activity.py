#!/usr/bin/env python3
"""Fetch public GitHub activity and build the Field Report activity plate.

Outputs:
  assets/activity-light.svg
  assets/activity-dark.svg
  docs/data/activity.json

The contribution calendar excludes restricted contributions; the plate is
labelled PUBLIC DATA. Only public repositories and public events are counted.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone

from fieldtype import DISPLAY, MONO, ROOT, text_path

LOGIN = os.environ.get("GITHUB_LOGIN", "Panharoth06")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"

W, H = 1280, 440
MATRIX_X, MATRIX_Y = 100, 166
CELL, GAP = 10, 3
STEP = CELL + GAP
COLUMNS = 53

THEMES = {
    "light": {
        "bg": "#E7E4DC",
        "ink": "#12161B",
        "muted": "#5B626B",
        "micro": "#4C535C",
        "accent": "#B23A2E",
        "grid": "rgba(18,22,27,0.055)",
        "rule": "rgba(18,22,27,0.18)",
        "rule_soft": "rgba(18,22,27,0.09)",
    },
    "dark": {
        "bg": "#12161B",
        "ink": "#E7E4DC",
        "muted": "#9AA0A6",
        "micro": "#B4B8BC",
        "accent": "#D2493C",
        "grid": "rgba(231,228,220,0.05)",
        "rule": "rgba(231,228,220,0.20)",
        "rule_soft": "rgba(231,228,220,0.10)",
    },
}

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
    repositories(first:100, privacy:PUBLIC, ownerAffiliations:OWNER, isFork:false,
                 orderBy:{field:UPDATED_AT, direction:DESC}) {
      totalCount
      nodes {
        name
        stargazerCount
        primaryLanguage { name }
      }
    }
  }
}
"""


def ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    # python.org builds on macOS do not always inherit the system roots.
    if os.path.exists("/etc/ssl/cert.pem"):
        try:
            context.load_verify_locations(cafile="/etc/ssl/cert.pem")
        except ssl.SSLError:
            pass
    return context


def github_request(url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {
        "Authorization": f"bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "field-report-builder",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45, context=ssl_context()) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"GitHub API {error.code}: {detail}") from error


def fetch() -> tuple[dict, list[dict]]:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required (locally: GITHUB_TOKEN=$(gh auth token)).")

    data = github_request(
        f"{API}/graphql",
        {"query": QUERY, "variables": {"login": LOGIN}},
    )
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"])[:600])

    user = data["data"]["user"]
    events = github_request(f"{API}/users/{LOGIN}/events/public?per_page=30")
    return user, events


def streak(days: list[dict]) -> tuple[int, int]:
    longest = current_run = best = 0
    for day in days:
        count = day["count"]
        if count > 0:
            current_run += 1
            longest = max(longest, current_run)
            best = max(best, count)
        else:
            current_run = 0

    current = 0
    index = len(days) - 1
    if index >= 0 and days[index]["count"] == 0:
        index -= 1
    while index >= 0 and days[index]["count"] > 0:
        current += 1
        index -= 1
    return current, longest


# Markup and configuration are excluded from the language index; this is a
# portfolio measure, not a byte count. Languages are ranked by how many public
# projects use them as their primary language.
EXCLUDED_LANGUAGES = {
    "HTML", "CSS", "SCSS", "Sass", "Less", "Stylus", "Shell", "Dockerfile",
    "Makefile", "Procfile", "Batchfile", "PowerShell", "Go Template",
}


def language_breakdown(nodes: list[dict]) -> list[dict]:
    counts: Counter[str] = Counter()
    for node in nodes:
        primary = node.get("primaryLanguage")
        if primary and primary["name"] not in EXCLUDED_LANGUAGES:
            counts[primary["name"]] += 1

    total = sum(counts.values())
    if total == 0:
        return []

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    selected = ranked[:4]
    other = total - sum(count for _, count in selected)
    groups = [{"name": name, "repos": count} for name, count in selected]
    if other > 0:
        groups.append({"name": "Other", "repos": other})

    # Largest-remainder rounding keeps the printed percentages at exactly 100.
    exact = [(group["repos"] / total) * 100 for group in groups]
    floors = [int(value) for value in exact]
    remainder = 100 - sum(floors)
    order = sorted(range(len(groups)), key=lambda i: exact[i] - floors[i], reverse=True)
    for i in order[:remainder]:
        floors[i] += 1
    for group, percent in zip(groups, floors):
        group["percent"] = percent
    return groups


def recent_events(events: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict] = []
    for event in events:
        kind = event.get("type", "")
        repo = event.get("repo", {}).get("name", "")
        created = event.get("created_at", "")
        payload = event.get("payload") or {}
        if not repo or not created:
            continue
        key = (kind, repo, created[:10])
        if key in seen:
            continue

        label = ""
        if kind == "PushEvent":
            count = payload.get("size") or len(payload.get("commits") or [])
            label = f"Pushed {count} commit{'s' if count != 1 else ''}" if count else "Pushed commits"
        elif kind == "PullRequestEvent":
            number = (payload.get("pull_request") or {}).get("number", "")
            action = payload.get("action", "")
            if action == "closed" and (payload.get("pull_request") or {}).get("merged"):
                label = f"Merged pull request #{number}"
            elif action:
                label = f"{action.capitalize()} pull request #{number}"
        elif kind == "IssuesEvent":
            number = (payload.get("issue") or {}).get("number", "")
            action = payload.get("action", "")
            if action:
                label = f"{action.capitalize()} issue #{number}"
        elif kind == "CreateEvent":
            ref_type = payload.get("ref_type", "")
            ref = payload.get("ref", "")
            label = f"Created {ref_type} {ref}".strip()
        elif kind == "ReleaseEvent":
            tag = (payload.get("release") or {}).get("tag_name", "")
            label = f"Published release {tag}".strip()
        elif kind == "WatchEvent":
            label = "Starred repository"
        elif kind == "ForkEvent":
            label = "Forked repository"

        if not label:
            continue

        seen.add(key)
        result.append(
            {
                "type": kind.replace("Event", ""),
                "label": label,
                "repo": repo,
                "date": created,
                "url": f"https://github.com/{repo}",
            }
        )
        if len(result) == 5:
            break
    return result


def build_data(user: dict, events: list[dict]) -> dict:
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    days = [
        {
            "date": day["date"],
            "count": day["contributionCount"],
            "weekday": day["weekday"],
        }
        for week in weeks
        for day in week["contributionDays"]
    ]
    days.sort(key=lambda day: day["date"])

    current, longest = streak(days)
    repos = user["repositories"]
    nodes = repos["nodes"]
    stars = sum(int(node["stargazerCount"]) for node in nodes)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "login": LOGIN,
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "totals": {
            "contributions": int(calendar["totalContributions"]),
            "currentStreak": current,
            "longestStreak": longest,
            "activeDays": sum(1 for day in days if day["count"] > 0),
            "bestDay": max((day["count"] for day in days), default=0),
            "publicProjects": int(repos["totalCount"]),
            "stars": stars,
        },
        "calendar": {
            "total": int(calendar["totalContributions"]),
            "weeks": [
                {
                    "days": [
                        {
                            "date": day["date"],
                            "count": day["contributionCount"],
                            "weekday": day["weekday"],
                        }
                        for day in week["contributionDays"]
                    ]
                }
                for week in weeks
            ],
        },
        "languages": language_breakdown(nodes),
        "recent": recent_events(events),
    }


def label(text: str, size: float, x: float, y: float, *, fill: str, font=MONO,
          tracking: float = 0.0, anchor: str = "start") -> str:
    d, _ = text_path(font, text, size, x=x, y=y, tracking=tracking, anchor=anchor)
    return f'<path d="{d}" fill="{fill}"/>'


def level(count: int) -> float:
    if count <= 0:
        return 0.07
    if count <= 2:
        return 0.18
    if count <= 5:
        return 0.34
    if count <= 9:
        return 0.55
    return 0.82


def month_starts(weeks: list[dict]) -> list[tuple[int, str]]:
    starts: list[tuple[int, str]] = []
    last_month = None
    for index, week in enumerate(weeks):
        days = week["days"]
        if not days:
            continue
        day = days[0]["date"]
        month = day[:7]
        if month != last_month:
            month_number = int(month[5:7])
            if month_number % 2 == 1:
                starts.append((index, date.fromisoformat(day).strftime("%b").upper()))
            last_month = month
    return starts


def build_svg(theme: str, data: dict) -> str:
    palette = THEMES[theme]
    ink = palette["ink"]
    muted = palette["muted"]
    micro = palette["micro"]
    accent = palette["accent"]
    weeks = data["calendar"]["weeks"]
    totals = data["totals"]
    languages = data["languages"]
    generated = datetime.fromisoformat(data["generatedAt"].replace("Z", "+00:00"))
    stamp = generated.strftime("%d %b %Y / %H:%M UTC").upper()

    cells: list[str] = []
    last_day = None
    for week_index, week in enumerate(weeks[:COLUMNS]):
        for day in week["days"]:
            weekday = int(day["weekday"])
            x = MATRIX_X + week_index * STEP
            y = MATRIX_Y + weekday * STEP
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{ink}" opacity="{level(int(day["count"]))}"/>'
            )
            last_day = day
    if last_day:
        weekday = int(last_day["weekday"])
        week_index = len(weeks[:COLUMNS]) - 1
        cells.append(
            f'<rect x="{MATRIX_X + week_index * STEP - 1}" y="{MATRIX_Y + weekday * STEP - 1}" '
            f'width="{CELL + 2}" height="{CELL + 2}" fill="none" stroke="{accent}" stroke-width="0.8"/>'
        )

    months = "".join(
        label(name, 8.5, MATRIX_X + index * STEP, 150, fill=muted, tracking=1.1)
        for index, name in month_starts(weeks)
    )

    day_labels = "".join(
        label(name, 8, MATRIX_X - 10, MATRIX_Y + row * STEP + 8,
              fill=muted, tracking=0.8, anchor="end")
        for name, row in (("MON", 1), ("WED", 3), ("FRI", 5))
    )

    legend_levels = [0.07, 0.18, 0.34, 0.55, 0.82]
    legend_squares = "".join(
        f'<rect x="{MATRIX_X + 46 + i * 16}" y="272" width="10" height="10" '
        f'fill="{ink}" opacity="{opacity}"/>'
        for i, opacity in enumerate(legend_levels)
    )

    lang_width = COLUMNS * STEP - GAP
    lang_bar_x = MATRIX_X
    lang_bar_y = 328
    lang_bar_h = 8
    segments: list[str] = []
    labels: list[str] = []
    x_cursor = lang_bar_x
    label_width = lang_width / max(1, len(languages))
    for index, language in enumerate(languages):
        width = (language["percent"] / 100) * lang_width
        color = accent if index == 0 else ink
        opacity = 1 if index == 0 else max(0.16, 0.55 - index * 0.1)
        label_x = lang_bar_x + index * label_width
        segments.append(
            f'<rect x="{x_cursor:.2f}" y="{lang_bar_y}" width="{max(0, width - 2):.2f}" '
            f'height="{lang_bar_h}" fill="{color}" opacity="{opacity:.2f}"/>'
        )
        labels.append(
            f'<rect x="{label_x:.2f}" y="344" width="4" height="4" fill="{color}" opacity="{opacity:.2f}"/>'
            + label(
                f'{language["name"].upper()} {language["percent"]}%',
                9,
                label_x + 9,
                350,
                fill=muted,
                tracking=0.9,
            )
        )
        x_cursor += width

    contributions = f"{totals['contributions']:,}"
    big_number = label(contributions, 94, 850, 212, fill=ink, font=DISPLAY, tracking=-2.5)
    big_label = label("CONTRIBUTIONS / LAST 12 MONTHS", 9.5, 850, 236,
                      fill=micro, tracking=1.7)

    stat_defs = [
        ("CURRENT STREAK", f"{totals['currentStreak']:02d} DAYS", 850),
        ("PUBLIC PROJECTS", f"{totals['publicProjects']}", 980),
        ("STARS", f"{totals['stars']:02d}", 1110),
    ]
    stats = "".join(
        label(name, 8, x, 292, fill=micro, tracking=1.25)
        + label(value, 17, x, 316, fill=ink, tracking=0.4)
        for name, value, x in stat_defs
    )

    header = (
        f'<rect x="72" y="49" width="6" height="6" fill="{accent}"/>'
        + label("FIELD LOG / ACTIVITY", 12, 88, 57, fill=muted, tracking=2.4)
        + label("LAST 12 MONTHS / PUBLIC DATA", 11.5, 1208, 57,
                fill=muted, tracking=1.61, anchor="end")
    )

    corners = (
        f'<g stroke="{muted}" stroke-width="1" fill="none" opacity="0.55">'
        f'<path d="M 30 44 V 30 H 44"/>'
        f'<path d="M 1236 30 H 1250 V 44"/>'
        f'<path d="M 30 396 V 410 H 44"/>'
        f'<path d="M 1236 410 H 1250 V 396"/>'
        f'</g>'
    )

    footer = (
        f'<line x1="72" y1="386" x2="1208" y2="386" stroke="{palette["rule"]}" stroke-width="1"/>'
        + label(f"SYNCED {stamp} / PUBLIC DATA", 9, 72, 404, fill=muted, tracking=1.1)
        + label("GITHUB / PANHAROTH06", 9, 1208, 404, fill=muted, tracking=1.1, anchor="end")
    )

    title = (
        f"Field log: {totals['contributions']:,} public contributions in the last 12 months, "
        f"a {totals['currentStreak']}-day current streak, {totals['publicProjects']} public projects, "
        f"and {totals['stars']} stars."
    )
    desc = (
        "A contribution matrix, activity figures, and project languages, set as a "
        "field-report plate. Generated from the public GitHub API."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">{title}</title>
  <desc id="d">{desc}</desc>
  <defs>
    <pattern id="grid" x="72" y="24" width="64" height="64" patternUnits="userSpaceOnUse">
      <path d="M 64 0 V 64 M 0 64 H 64" fill="none" stroke="{palette['grid']}" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{W}" height="{H}" fill="{palette['bg']}"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  {corners}
  {header}
  {months}
  {day_labels}
  {''.join(cells)}
  {label("LESS", 8, MATRIX_X, 281, fill=muted, tracking=1.2)}
  {legend_squares}
  {label("MORE", 8, MATRIX_X + 46 + len(legend_levels) * 16 + 4, 281, fill=muted, tracking=1.2)}
  {label("LANGUAGES / BY PROJECT", 9, MATRIX_X, 312, fill=micro, tracking=1.5)}
  {''.join(segments)}
  {''.join(labels)}
  {big_number}
  {big_label}
  {stats}
  {footer}
</svg>
"""


def update_readme(generated_at: str) -> None:
    """Version the activity image URLs so GitHub's Camo cache re-fetches them."""
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    generated = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    version = generated.strftime("%Y%m%d%H%M")
    block = f"""<!-- activity:start -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/activity-dark.svg?v={version}">
  <img src="assets/activity-light.svg?v={version}" width="100%" alt="Field log of public GitHub activity: contribution matrix, current streak, public project count, stars, and a project language index. Updated daily.">
</picture>
<!-- activity:end -->"""
    pattern = re.compile(r"<!-- activity:start -->.*?<!-- activity:end -->", re.S)
    if not pattern.search(text):
        raise RuntimeError("README activity markers not found")
    path.write_text(pattern.sub(block, text, count=1), encoding="utf-8")
    print("README.md activity block updated")


def main() -> None:
    user, events = fetch()
    data = build_data(user, events)

    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    data_dir = ROOT / "docs" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "activity.json").write_text(payload, encoding="utf-8")

    for theme in THEMES:
        svg = build_svg(theme, data)
        path = ROOT / "assets" / f"activity-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}  {len(svg) / 1024:.1f} KB")

    update_readme(data["generatedAt"])

    print(f"docs/data/activity.json  {len(payload) / 1024:.1f} KB")
    print(
        f"{data['totals']['contributions']} contributions / "
        f"{data['totals']['currentStreak']}d streak / "
        f"{data['totals']['publicProjects']} public projects / "
        f"{data['totals']['stars']} stars"
    )


if __name__ == "__main__":
    main()
