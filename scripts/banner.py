#!/usr/bin/env python3
"""Profil başlığı için anime temalı, animasyonlu banner (assets/banner.svg)."""
import random

from anime import FONT, hero, petals, sparkle, sparkles
from common import ASSETS


def blossom(x, y, r, rnd):
    petals_ = "".join(
        f'<circle cx="{x + r * 0.9 * __import__("math").cos(a):.1f}" cy="{y + r * 0.9 * __import__("math").sin(a):.1f}" r="{r * 0.62:.1f}" fill="#ffb7d5"/>'
        for a in [i * 1.2566 + rnd.uniform(-0.1, 0.1) for i in range(5)]
    )
    return petals_ + f'<circle cx="{x}" cy="{y}" r="{r * 0.28:.1f}" fill="#ff6fae"/>'


def build() -> str:
    W, H = 900, 240
    rnd = random.Random(21)
    branch = (
        '<path d="M-10,34 Q140,18 250,70 T470,66" fill="none" stroke="#3b1f4f" stroke-width="9" stroke-linecap="round"/>'
        '<path d="M120,26 Q150,60 190,64" fill="none" stroke="#3b1f4f" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M300,76 Q330,112 372,118" fill="none" stroke="#3b1f4f" stroke-width="5" stroke-linecap="round"/>'
    )
    blossoms = "".join(
        blossom(x, y, r, rnd)
        for x, y, r in [(40, 30, 11), (90, 24, 12), (150, 38, 10), (190, 64, 12), (232, 70, 11), (300, 78, 12),
                        (372, 118, 11), (350, 72, 10), (430, 66, 12), (130, 58, 9), (270, 88, 9)]
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" role="img" aria-label="Sakura gecesi banner">'
        '<defs>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#120d4f"/>'
        '<stop offset="0.6" stop-color="#4b2182"/><stop offset="1" stop-color="#e0559a"/></linearGradient>'
        '<radialGradient id="moon" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff6d6"/>'
        '<stop offset="0.55" stop-color="#ffe9a8" stop-opacity="0.9"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="clip"><rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="20"/></clipPath>'
        '</defs>'
        '<g clip-path="url(#clip)">'
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
        f'<circle cx="560" cy="86" r="120" fill="url(#moon)"/>'
        + sparkles(W, H, 34, seed=9, color="#ffffff")
        # uzak siluet
        + f'<path d="M0,{H} L0,196 Q80,170 150,192 T300,186 T460,196 T640,180 T800,194 T{W},182 L{W},{H}Z" fill="#241046" opacity="0.85"/>'
        + f'<path d="M0,{H} L0,214 Q120,196 240,212 T520,208 T800,214 T{W},206 L{W},{H}Z" fill="#150a2e"/>'
        + branch + blossoms
        + petals(W, H, 22, seed=5)
        # yazı
        + '<text x="330" y="128" fill="none" font-size="36" font-weight="bold" font-style="italic" stroke="#5b1f78" stroke-width="7" stroke-linejoin="round">Code · Anime · Games</text>'
        + '<text x="330" y="128" fill="#ffffff" font-size="36" font-weight="bold" font-style="italic">Code · Anime · Games</text>'
        + '<text x="334" y="158" fill="#ffd1e8" font-size="15" font-style="italic">building things that actually work</text>'
        + hero(W - 178, 56, 0.72, "bh")
        + sparkle(W - 60, 70, 9, "#fff7b0", 0.2) + sparkle(W - 200, 120, 6, "#ffffff", 1.2)
        + '</g>'
        f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="20" fill="none" stroke="#ffd1e8" stroke-width="3" opacity="0.8"/>'
        '</svg>'
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "banner.svg").write_text(build(), encoding="utf-8")
    print("Yazildi: assets/banner.svg")


if __name__ == "__main__":
    main()
