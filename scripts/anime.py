"""Anime estetiği için ortak SVG parçaları: sakura yaprakları, parıltılar, chibi karakter, chibi boss.

Hepsi orijinal çizimler; belirli bir anime/oyun karakterine dayanmaz.
SMIL animasyonları GitHub'da <img> içinde de çalışır; statik önizlemede (cairosvg) yaprak/parıltılar sabit görünür.
"""
import math
import random

FONT = "'Trebuchet MS','Segoe UI',Verdana,sans-serif"


def sparkle(x, y, r, color="#ffffff", delay=0.0, dur=2.4):
    d = (f"M{x:.1f},{y - r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y + r:.1f} "
         f"Q{x:.1f},{y:.1f} {x - r:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y - r:.1f}Z")
    return (f'<path d="{d}" fill="{color}"><animate attributeName="opacity" values="0.15;1;0.15" '
            f'dur="{dur}s" begin="-{delay:.1f}s" repeatCount="indefinite"/></path>')


def sparkles(W, H, n=14, seed=3, color="#ffffff"):
    rnd = random.Random(seed)
    return "".join(
        sparkle(rnd.uniform(10, W - 10), rnd.uniform(10, H - 10), rnd.uniform(2.5, 6.5), color,
                rnd.uniform(0, 3), rnd.uniform(1.8, 3.6))
        for _ in range(n)
    )


def petals(W, H, n=14, seed=1):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x = rnd.uniform(0, W)
        y0 = rnd.uniform(0, H)
        s = rnd.uniform(5, 10)
        dur = rnd.uniform(8, 14)
        delay = rnd.uniform(0, dur)
        drift = rnd.uniform(-70, 70)
        color = rnd.choice(["#ffc1dc", "#ffb0d0", "#ffd6e8", "#ff9fc4"])
        path = f"M0,0 Q{s * 0.7:.1f},{-s * 0.5:.1f} {s * 1.1:.1f},{s * 0.4:.1f} Q{s * 0.5:.1f},{s:.1f} 0,0Z"
        out.append(
            f'<g transform="translate({x:.0f},{y0:.0f})" opacity="0.85">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{x:.0f},-20;{x + drift:.0f},{H + 20}" dur="{dur:.1f}s" begin="-{delay:.1f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="rotate" values="0;360" '
            f'dur="{rnd.uniform(4, 8):.1f}s" additive="sum" repeatCount="indefinite"/>'
            f'<path d="{path}" fill="{color}"/></g>'
        )
    return "".join(out)


def burst(cx, cy, r_out, r_in, points=12, fill="#ffeb3b", stroke="#ff5722", rot=0.0):
    """Çizgi roman tarzı vuruş patlaması (yıldız çokgeni)."""
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / points
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="3" stroke-linejoin="round"/>'


def speed_lines(cx, cy, W, H, n=36, seed=5, color="#ffffff", opacity=0.12):
    rnd = random.Random(seed)
    out = []
    far = math.hypot(W, H)
    for _ in range(n):
        a = rnd.uniform(0, math.tau)
        r0 = rnd.uniform(70, 140)
        w = rnd.uniform(0.01, 0.03)
        p1 = (cx + r0 * math.cos(a - w), cy + r0 * math.sin(a - w))
        p2 = (cx + r0 * math.cos(a + w), cy + r0 * math.sin(a + w))
        p3 = (cx + far * math.cos(a), cy + far * math.sin(a))
        out.append(f'<polygon points="{p1[0]:.0f},{p1[1]:.0f} {p2[0]:.0f},{p2[1]:.0f} {p3[0]:.0f},{p3[1]:.0f}" '
                   f'fill="{color}" opacity="{opacity}"/>')
    return "".join(out)


def hero(x, y, scale=1.0, pre="h"):
    """Orijinal chibi büyücü: büyük parlak gözler, ahoge, yıldız tokası. Yerel kutu: 200x240."""
    eye = lambda cx: (
        f'<ellipse cx="{cx}" cy="108" rx="16" ry="20" fill="#ffffff"/>'
        f'<ellipse cx="{cx}" cy="110" rx="12.5" ry="17.5" fill="url(#{pre}iris)"/>'
        f'<ellipse cx="{cx}" cy="112" rx="6" ry="10.5" fill="#1b1442"/>'
        f'<circle cx="{cx - 5}" cy="101" r="4.6" fill="#ffffff"/>'
        f'<circle cx="{cx + 4.5}" cy="118" r="2.3" fill="#ffffff" opacity="0.9"/>'
        f'<path d="M{cx - 18},{104} Q{cx},{84} {cx + 18},{104}" fill="none" stroke="#2a1d5a" stroke-width="4" stroke-linecap="round"/>'
    )
    return (
        f'<g transform="translate({x},{y}) scale({scale})">'
        f'<defs>'
        f'<linearGradient id="{pre}hair" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8e6bff"/><stop offset="1" stop-color="#3a2a9c"/></linearGradient>'
        f'<linearGradient id="{pre}robe" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4fa3ff"/><stop offset="1" stop-color="#2c4fd1"/></linearGradient>'
        f'<radialGradient id="{pre}iris" cx="0.5" cy="0.3" r="0.8"><stop offset="0" stop-color="#7ef3ff"/><stop offset="0.6" stop-color="#3f8cff"/><stop offset="1" stop-color="#6a3fd1"/></radialGradient>'
        f'</defs>'
        # arka saç
        f'<path d="M30,104 Q26,28 100,22 Q174,28 170,104 Q176,160 148,188 Q142,140 100,136 Q58,140 52,188 Q24,160 30,104Z" fill="url(#{pre}hair)"/>'
        # gövde / pelerin
        f'<path d="M58,176 Q100,152 142,176 L154,236 Q100,250 46,236Z" fill="url(#{pre}robe)"/>'
        f'<path d="M84,178 L100,206 L116,178 Q100,170 84,178Z" fill="#ffffff" opacity="0.9"/>'
        f'<path d="M90,190 Q100,200 110,190 L112,214 Q100,222 88,214Z" fill="#ff7eb3"/>'
        f'<circle cx="100" cy="200" r="5.5" fill="#ffd54f" stroke="#ffffff" stroke-width="1.5"/>'
        # yüz
        f'<ellipse cx="100" cy="102" rx="62" ry="56" fill="#ffe6d6"/>'
        f'<ellipse cx="100" cy="150" rx="40" ry="10" fill="#f6c9b3" opacity="0.35"/>'
        + eye(72) + eye(128) +
        f'<ellipse cx="54" cy="132" rx="11" ry="6" fill="#ff8fb1" opacity="0.55"/>'
        f'<ellipse cx="146" cy="132" rx="11" ry="6" fill="#ff8fb1" opacity="0.55"/>'
        f'<path d="M91,138 Q100,148 109,138" fill="none" stroke="#c4566e" stroke-width="3" stroke-linecap="round"/>'
        # kâkül
        f'<path d="M34,100 Q38,34 100,30 Q162,34 166,100 Q152,76 138,84 L128,58 L113,88 L100,54 L87,88 L72,58 L62,84 Q48,76 34,100Z" fill="url(#{pre}hair)"/>'
        f'<path d="M70,50 Q96,36 128,48" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.45"/>'
        # ahoge
        f'<path d="M100,34 Q86,6 112,2 Q100,16 108,32" fill="url(#{pre}hair)" stroke="#3a2a9c" stroke-width="1"/>'
        # yıldız tokası
        f'<path d="M58,56 L61,48 L64,56 L72,58 L64,61 L61,70 L58,61 L50,58Z" fill="#ffd54f" stroke="#ffffff" stroke-width="1.2"/>'
        f'</g>'
    )


def demon(x, y, scale, body="#7e57c2", accent="#ffd54f", variant=0, pre="d"):
    """Orijinal chibi 'boss' (şeytan lordu tarzı). Yerel kutu: 220x230. variant: 0 taç, 1 hale, 2 üçüncü göz."""
    deco = [
        # taç
        f'<path d="M72,40 L82,16 L96,36 L110,10 L124,36 L138,16 L148,40Z" fill="{accent}" stroke="#ffffff" stroke-width="1.5"/>',
        # hale
        f'<ellipse cx="110" cy="22" rx="42" ry="10" fill="none" stroke="{accent}" stroke-width="5"/>',
        # üçüncü göz
        f'<ellipse cx="110" cy="64" rx="8" ry="11" fill="#ffffff"/><ellipse cx="110" cy="65" rx="4.5" ry="8" fill="{accent}"/><ellipse cx="110" cy="66" rx="1.8" ry="5" fill="#2b0a0a"/>',
    ][variant % 3]
    eye = lambda cx, flip: (
        f'<ellipse cx="{cx}" cy="108" rx="15" ry="17" fill="#ffffff"/>'
        f'<ellipse cx="{cx}" cy="109" rx="11" ry="15" fill="url(#{pre}eye)"/>'
        f'<ellipse cx="{cx}" cy="109" rx="3.2" ry="12" fill="#1a0505"/>'
        f'<circle cx="{cx - 4}" cy="102" r="3.6" fill="#ffffff"/>'
        f'<path d="M{cx - 20},{92 - flip * 6} L{cx + 20},{92 + flip * 6 + 6}" stroke="#2b0a0a" stroke-width="5" stroke-linecap="round"/>'
    )
    return (
        f'<g transform="translate({x},{y}) scale({scale})">'
        f'<defs>'
        f'<radialGradient id="{pre}aura" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{body}" stop-opacity="0.6"/><stop offset="1" stop-color="{body}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="{pre}eye" cx="0.5" cy="0.3" r="0.8"><stop offset="0" stop-color="#fff59d"/><stop offset="0.6" stop-color="#ff7043"/><stop offset="1" stop-color="#c62828"/></radialGradient>'
        f'<linearGradient id="{pre}cape" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b1f5c"/><stop offset="1" stop-color="#16081f"/></linearGradient>'
        f'</defs>'
        f'<circle cx="110" cy="118" r="120" fill="url(#{pre}aura)"/>'
        # pelerin + gövde
        f'<path d="M36,236 Q30,170 66,160 L154,160 Q190,170 184,236Z" fill="url(#{pre}cape)" stroke="{accent}" stroke-width="2"/>'
        f'<path d="M92,164 L110,196 L128,164Z" fill="{accent}"/>'
        # boynuzlar
        f'<path d="M58,78 Q34,52 40,18 Q62,40 78,66Z" fill="{accent}" stroke="#ffffff" stroke-width="1.5"/>'
        f'<path d="M162,78 Q186,52 180,18 Q158,40 142,66Z" fill="{accent}" stroke="#ffffff" stroke-width="1.5"/>'
        # kafa
        f'<ellipse cx="110" cy="112" rx="66" ry="58" fill="{body}"/>'
        f'<ellipse cx="110" cy="150" rx="44" ry="10" fill="#000000" opacity="0.12"/>'
        + eye(80, 1) + eye(140, -1) +
        # sivri dişli sırıtış
        f'<path d="M80,142 Q110,166 140,142 Q110,152 80,142Z" fill="#2b0a0a"/>'
        f'<path d="M90,146 L95,155 L100,148Z M120,148 L125,155 L130,146Z" fill="#ffffff"/>'
        f'<ellipse cx="62" cy="134" rx="10" ry="5" fill="#ff6e9c" opacity="0.4"/>'
        f'<ellipse cx="158" cy="134" rx="10" ry="5" fill="#ff6e9c" opacity="0.4"/>'
        + deco +
        f'</g>'
    )
