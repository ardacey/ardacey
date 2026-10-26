#!/usr/bin/env python3
"""GitHub istatistiklerinden anime/JRPG tarzı bir karakter karti (SVG) uretir.

Kullanim:
    python scripts/rpg_card.py --user ardacey          # GitHub API'den gercek veri
    python scripts/rpg_card.py --demo                  # API'siz ornek veri (test icin)
"""
import argparse
import datetime
import json
import math
import os
import urllib.request
from collections import Counter
from xml.sax.saxutils import escape

from anime import FONT, hero, petals, sparkle, sparkles
from common import ASSETS

API = "https://api.github.com"

CLASS_BY_LANG = {
    "Python": "Piton Büyücüsü",
    "Jupyter Notebook": "Simyacı",
    "JavaScript": "Web Gölge Hırsızı",
    "TypeScript": "Tip Kâhini",
    "Java": "Paladin",
    "Kotlin": "Okçu",
    "C++": "Berserker",
    "C": "Demirci",
    "Go": "Gezgin Şövalye",
    "Rust": "Zırhlı Şövalye",
}


def api(path: str, token: str | None):
    req = urllib.request.Request(
        API + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "rpg-card"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch(user: str, token: str | None) -> dict:
    profile = api(f"/users/{user}", token)
    repos, page = [], 1
    while True:
        batch = api(f"/users/{user}/repos?per_page=100&type=owner&page={page}", token)
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    repos = [r for r in repos if not r.get("fork")]
    try:
        commits = api(f"/search/commits?q=author:{user}&per_page=1", token)["total_count"]
    except Exception:
        commits = 0
    langs = Counter(r["language"] for r in repos if r.get("language"))
    return {
        "name": profile.get("name") or user,
        "login": user,
        "repos": len(repos),
        "stars": sum(r.get("stargazers_count", 0) for r in repos),
        "followers": profile.get("followers", 0),
        "commits": commits,
        "langs": langs,
    }


def demo_data() -> dict:
    return {
        "name": "Arda Ceylan", "login": "ardacey", "repos": 39, "stars": 6,
        "followers": 125, "commits": 1100,
        "langs": Counter({"Python": 12, "Jupyter Notebook": 7, "TypeScript": 5,
                          "Kotlin": 3, "Java": 4, "JavaScript": 3}),
    }


def xp_for_level(level: int) -> int:
    return 60 * (level - 1) ** 2


def compute(d: dict) -> dict:
    xp = d["commits"] * 10 + d["stars"] * 50 + d["repos"] * 20 + d["followers"] * 15
    level = int(math.sqrt(xp / 60)) + 1
    lo, hi = xp_for_level(level), xp_for_level(level + 1)
    progress = (xp - lo) / (hi - lo) if hi > lo else 0
    top = d["langs"].most_common(3)
    cls = CLASS_BY_LANG.get(top[0][0], "Gezgin") if top else "Gezgin"
    ds_repos = d["langs"].get("Jupyter Notebook", 0) + d["langs"].get("Python", 0)
    stats = [
        ("STR", d["commits"], 2000),
        ("INT", ds_repos, 20),
        ("DEX", len(d["langs"]), 10),
        ("WIS", d["followers"], 500),
        ("LUK", d["stars"], 50),
    ]
    return {"xp": xp, "level": level, "progress": progress, "class": cls,
            "top": top, "stats": stats, "lo": lo, "hi": hi}


def pill(x, y, w, text, fill, color="#ffffff", size=12):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="11" fill="{fill}" opacity="0.9"/>'
        f'<text x="{x + w / 2}" y="{y + 15}" fill="{color}" font-size="{size}" font-weight="bold" text-anchor="middle">{text}</text>'
    )


def gbar(x, y, w, h, frac, c1, c2, uid):
    frac = max(0.0, min(1.0, frac))
    return (
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="#ffffff" opacity="0.14"/>'
        f'<rect x="{x}" y="{y}" width="{max(h, w * frac):.1f}" height="{h}" rx="{h / 2}" fill="url(#{uid})"/>'
        f'<rect x="{x + 3}" y="{y + 2}" width="{max(0, w * frac - 6):.1f}" height="{max(1, h / 4):.1f}" rx="{h / 8}" fill="#ffffff" opacity="0.35"/>'
    )


def render(d: dict, c: dict) -> str:
    W, H = 640, 330
    today = datetime.date.today().isoformat()
    P = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" role="img" aria-label="Anime RPG karakter kartı">',
        '<defs>'
        '<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b1464"/>'
        '<stop offset="0.55" stop-color="#5b2a86"/><stop offset="1" stop-color="#d1478f"/></linearGradient>'
        '<radialGradient id="moon" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff6d6"/>'
        '<stop offset="0.6" stop-color="#ffe9a8" stop-opacity="0.9"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="frame" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd1e8"/>'
        '<stop offset="1" stop-color="#a98bff"/></linearGradient>'
        f'<clipPath id="clip"><rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="18"/></clipPath>'
        '</defs>',
        f'<g clip-path="url(#clip)">',
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
        f'<circle cx="{W - 90}" cy="70" r="90" fill="url(#moon)"/>',
        sparkles(W, H, 22, seed=7),
        petals(W, H, 16, seed=2),
        # sol: karakter çerçevesi
        '<rect x="22" y="22" width="190" height="228" rx="16" fill="#ffffff" opacity="0.12"/>',
        '<rect x="22" y="22" width="190" height="228" rx="16" fill="none" stroke="url(#frame)" stroke-width="3"/>',
        hero(24, 16, 0.95),
        sparkle(36, 44, 7, "#ffffff", 0.3), sparkle(196, 70, 5, "#ffd1e8", 1.1), sparkle(190, 226, 6, "#ffffff", 0.7),
        # sağ: isim, sınıf, seviye
        f'<text x="236" y="56" fill="none" font-size="28" font-weight="bold" font-style="italic" '
        f'stroke="#7b2d8e" stroke-width="6" stroke-linejoin="round">{escape(d["name"])}</text>'
        f'<text x="236" y="56" fill="#ffffff" font-size="28" font-weight="bold" font-style="italic">{escape(d["name"])}</text>',
    ]
    P.append(pill(236, 66, max(120, 9 * len(c["class"]) + 24), escape(c["class"]), "#ff6fae"))
    # seviye rozeti
    P.append(
        f'<circle cx="{W - 62}" cy="52" r="30" fill="#ffd54f" stroke="#ffffff" stroke-width="3"/>'
        f'<circle cx="{W - 62}" cy="52" r="24" fill="none" stroke="#ff8f00" stroke-width="2" stroke-dasharray="3 4"/>'
        f'<text x="{W - 62}" y="46" fill="#7a3d00" font-size="10" font-weight="bold" text-anchor="middle">LEVEL</text>'
        f'<text x="{W - 62}" y="68" fill="#7a3d00" font-size="24" font-weight="bold" font-style="italic" text-anchor="middle">{c["level"]}</text>'
    )
    # EXP
    P.append(f'<text x="236" y="112" fill="#ffe3f1" font-size="12" font-weight="bold">EXP  {c["xp"]:,} / {c["hi"]:,}</text>')
    P.append(gbar(236, 118, W - 236 - 28, 12, c["progress"], "#ff9ecb", "#ffd54f", "exp"))
    # statlar
    cols = [("#ff6b6b", "#ffa07a"), ("#4dd0e1", "#7c8cff"), ("#69f0ae", "#c6ff00"), ("#d281ff", "#ff7eb3"), ("#ffca28", "#ff8a65")]
    names = {"STR": "Güç", "INT": "Zeka", "DEX": "Çeviklik", "WIS": "Bilgelik", "LUK": "Şans"}
    y = 152
    for i, (lab, val, cap) in enumerate(c["stats"]):
        P.append(f'<text x="236" y="{y + 11}" fill="#ffffff" font-size="12" font-weight="bold">{lab}</text>')
        P.append(f'<text x="266" y="{y + 11}" fill="#e8d9ff" font-size="11">{names[lab]}</text>')
        P.append(gbar(344, y, 190, 12, val / cap, cols[i][0], cols[i][1], f"s{i}"))
        P.append(f'<text x="544" y="{y + 11}" fill="#ffe3f1" font-size="12" font-weight="bold">{val:,}</text>')
        y += 22
    # beceriler (pill)
    P.append('<text x="24" y="276" fill="#ffd1e8" font-size="12" font-weight="bold">SKILLS</text>')
    px = 82
    palette = ["#ff6fae", "#7c8cff", "#43c6ac"]
    for i, (lang, n) in enumerate(c["top"]):
        label = escape(f'{lang.replace("Jupyter ", "")} x{n}')
        w = 9 * len(label) + 20
        P.append(pill(px, 261, w, label, palette[i % 3]))
        px += w + 8
    P.append(f'<text x="{W - 22}" y="{H - 14}" fill="#e8d9ff" font-size="10" text-anchor="end" opacity="0.8">@{escape(d["login"])} · {today}</text>')
    P.append('</g>')
    P.append(f'<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="18" fill="none" stroke="url(#frame)" stroke-width="3"/>')
    P.append('</svg>')
    return "".join(P)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "ardacey"))
    ap.add_argument("--out", default=str(ASSETS / "rpg-card.svg"))
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    data = demo_data() if args.demo else fetch(args.user, os.environ.get("GITHUB_TOKEN"))
    card = compute(data)
    svg = render(data, card)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Yazildi: {args.out} (Lv {card['level']}, {card['class']})")


if __name__ == "__main__":
    main()
