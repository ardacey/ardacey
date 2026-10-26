"""Builds assets/lights.svg: a night skyline with a passing train, where every
follower and stargazer of the profile gets a window lit in their name.

Also rewrites the visitor line in README.md between the LIGHTS markers.
Runs hourly and on every new star from .github/workflows/lights.yml.

Env:
  GITHUB_TOKEN   token for the GitHub API (optional, raises the rate limit)
  LIGHTS_OFFLINE rebuild from visitors.json without calling the API
"""
import json, os, random, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VISITORS = os.path.join(HERE, 'visitors.json')
OWNER = 'ardacey'
W, H = 1024, 220
DECK = 150            # top of the elevated railway
WARM = '#ffcf7a'      # visitor windows
LOGIN = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})')

def load():
    try:
        with open(VISITORS) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def api_logins(path):
    logins, page = [], 1
    while True:
        req = urllib.request.Request(f'https://api.github.com{path}?per_page=100&page={page}',
                                     headers={'Accept': 'application/vnd.github+json'})
        if os.environ.get('GITHUB_TOKEN'):
            req.add_header('Authorization', 'Bearer ' + os.environ['GITHUB_TOKEN'])
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        logins += [u['login'] for u in batch if u.get('type') == 'User']
        if len(batch) < 100:
            return logins
        page += 1

def sync():
    """Append new followers and stargazers. Lit windows stay lit, in their place."""
    visitors = load()
    known = {v.lower() for v in visitors}
    for login in api_logins(f'/users/{OWNER}/followers') + api_logins(f'/repos/{OWNER}/{OWNER}/stargazers'):
        if LOGIN.fullmatch(login) and login.lower() not in known and login.lower() != OWNER:
            visitors.append(login)
            known.add(login.lower())
    with open(VISITORS, 'w') as f:
        json.dump(visitors, f, indent=1)
        f.write('\n')
    return visitors

# ---------- skyline ----------
def buildings(rng, tops, widths, x0=-20):
    out, x = [], x0
    while x < W + 20:
        w = rng.randint(*widths)
        out.append((x, rng.randint(*tops), w))
        x += w + rng.randint(0, 6)
    return out

def windows(rng, blds, size, gap, max_y):
    """Window slots (x, y, w, h) on building faces, above max_y."""
    ww, wh = size
    out = []
    for x, top, w in blds:
        cols = max(1, int((w - 6) // (ww + gap)))
        pad = (w - cols * (ww + gap) + gap) / 2
        y = top + 6
        while y + wh < max_y:
            for c in range(cols):
                out.append((x + pad + c * (ww + gap), y, ww, wh))
            y += wh + gap + 1
    return out

def build(visitors):
    rng = random.Random(42)
    far = buildings(rng, (52, 118), (26, 64))
    mid = buildings(rng, (84, 140), (34, 80), x0=-35)
    near = buildings(rng, (182, 204), (50, 120), x0=-10)
    far_win = windows(rng, far, (2, 3), 4, DECK - 4)
    mid_win = windows(rng, mid, (3, 4), 5, DECK - 2)

    # visitor slots: a fixed shuffled order of mid-layer windows, so lights never move
    slots = mid_win[:]
    random.Random(7).shuffle(slots)
    lit = {slots[i] for i in range(min(len(visitors), len(slots)))}

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    o.append(f'''<style>
  .tw {{ animation: tw 6s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: .9; }} }}
  .blink {{ animation: blink 2.2s steps(1) infinite; }}
  @keyframes blink {{ 0%,60% {{ opacity: 1; }} 61%,100% {{ opacity: .15; }} }}
  .train {{ animation: ride 16s linear infinite; }}
  @keyframes ride {{ 0% {{ transform: translateX(-560px); }} 55%,100% {{ transform: translateX({W + 40}px); }} }}
  .rain {{ animation: fall 1.4s linear infinite; }}
  @keyframes fall {{ from {{ transform: translateY(0); }} to {{ transform: translateY({H}px); }} }}
</style>
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#070914"/><stop offset="0.65" stop-color="#16123a"/><stop offset="1" stop-color="#3a1a4a"/>
  </linearGradient>
  <linearGradient id="fog" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a1d4a" stop-opacity="0"/><stop offset="1" stop-color="#2a1d4a" stop-opacity="0.55"/>
  </linearGradient>
  <radialGradient id="haze" cx="0.5" cy="1" r="0.75">
    <stop offset="0" stop-color="#ff5fa2" stop-opacity="0.4"/><stop offset="0.5" stop-color="#5a3aa8" stop-opacity="0.12"/><stop offset="1" stop-color="#000" stop-opacity="0"/>
  </radialGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="soft" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="6"/></filter>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<rect y="20" width="{W}" height="{DECK}" fill="url(#haze)"/>''')

    # far layer
    o.append('<g fill="#141936">' + ''.join(f'<rect x="{x}" y="{t}" width="{w}" height="{H - t}"/>' for x, t, w in far) + '</g>')
    amb = rng.sample(far_win, len(far_win) // 4)
    o.append('<g fill="#8fb8ff" opacity="0.35">' + ''.join(f'<rect x="{x:.1f}" y="{y}" width="{w}" height="{h}"/>' for x, y, w, h in amb) + '</g>')

    # mid layer + windows
    o.append('<g fill="#0d1026">' + ''.join(f'<rect x="{x}" y="{t}" width="{w}" height="{H - t}"/>' for x, t, w in mid) + '</g>')
    free = [s for s in mid_win if s not in lit]
    amb = rng.sample(free, len(free) // 3)
    twinkle = set(rng.sample(amb, min(24, len(amb))))
    colors = ['#5ee7f2', '#ff5fa2', '#c8d6ff', '#c8d6ff', '#c8d6ff']
    for x, y, w, h in amb:
        cls = f' class="tw" style="animation-delay:{rng.uniform(0, 6):.1f}s"' if (x, y, w, h) in twinkle else ''
        o.append(f'<rect{cls} x="{x:.1f}" y="{y}" width="{w}" height="{h}" fill="{rng.choice(colors)}" opacity="0.55"/>')

    # visitor windows: warm and steady, with a soft halo
    if lit:
        halo = ''.join(f'<rect x="{x - 2:.1f}" y="{y - 2}" width="{w + 4}" height="{h + 4}"/>' for x, y, w, h in lit)
        o.append(f'<g fill="{WARM}" filter="url(#glow)">{halo}</g>')
        o.append(f'<g fill="{WARM}">' + ''.join(f'<rect x="{x:.1f}" y="{y}" width="{w}" height="{h}"/>' for x, y, w, h in lit) + '</g>')

    # a few vertical neon signs
    for x, t, w in rng.sample([b for b in mid if b[2] > 44 and b[1] < 110], 5):
        sx, color = x + w - 7, rng.choice(['#ff5fa2', '#5ee7f2', '#ffa45c'])
        o.append(f'<rect x="{sx}" y="{t + 10}" width="4" height="26" rx="1" fill="{color}" filter="url(#glow)" opacity="0.8"/>'
                 f'<rect x="{sx}" y="{t + 10}" width="4" height="26" rx="1" fill="{color}" opacity="0.9"/>')

    # aviation lights on the tallest mid buildings
    for i, (x, t, w) in enumerate(sorted(mid, key=lambda b: b[1])[:3]):
        o.append(f'<circle class="blink" style="animation-delay:{i * 0.7:.1f}s" cx="{x + w / 2:.1f}" cy="{t - 2}" r="1.6" fill="#ff3b3b"/>')

    # elevated railway
    o.append(f'<rect x="0" y="{DECK}" width="{W}" height="7" fill="#07081a"/>')
    o.append(f'<rect x="0" y="{DECK}" width="{W}" height="1" fill="#2c3160"/>')
    o.append('<g fill="#07081a">' + ''.join(f'<rect x="{x}" y="{DECK + 7}" width="6" height="{H - DECK}"/>' for x in range(10, W, 64)) + '</g>')

    # train: four cars with lit windows, a soft light trail on the deck
    cars = []
    for c in range(4):
        cx = c * 128
        cars.append(f'<rect x="{cx}" y="{DECK - 15}" width="124" height="15" rx="3" fill="#0a0c1e"/>')
        cars.append(f'<rect x="{cx}" y="{DECK - 4}" width="124" height="1.2" fill="#5ee7f2" opacity="0.5"/>')
        cars.append(''.join(f'<rect x="{cx + 7 + k * 13}" y="{DECK - 12}" width="8" height="5" rx="1" fill="#ffd9a0" opacity="0.92"/>' for k in range(9)))
    cars.append(f'<circle cx="510" cy="{DECK - 6}" r="2" fill="#fff4d6"/><rect x="510" y="{DECK - 9}" width="60" height="6" fill="#fff4d6" opacity="0.35" filter="url(#soft)"/>')
    o.append(f'<g class="train"><rect x="0" y="{DECK - 12}" width="506" height="10" fill="#ffe7b8" opacity="0.35" filter="url(#soft)"/>'
             + ''.join(cars) + '</g>')

    # near rooftops in front
    o.append(f'<rect width="{W}" height="{H}" fill="url(#fog)"/>')
    o.append('<g fill="#0a0b19">' + ''.join(f'<rect x="{x}" y="{t}" width="{w}" height="{H - t}"/>' for x, t, w in near) + '</g>')
    near_win = rng.sample(windows(rng, near, (3, 4), 6, H - 2), 14)
    o.append('<g fill="#ffcf9a" opacity="0.6">' + ''.join(f'<rect x="{x:.1f}" y="{y}" width="{w}" height="{h}"/>' for x, y, w, h in near_win) + '</g>')

    # light rain, same mood as the banner
    lines = []
    for _ in range(60):
        x, y = rng.uniform(-20, W), rng.uniform(0, H)
        for dy in (0, -H):
            lines.append(f'M{x:.1f},{y + dy:.1f} l-2.4,20')
    o.append(f'<g class="rain" opacity="0.12"><path d="{" ".join(lines)}" stroke="#d6ecff" stroke-width="0.8"/></g>')
    o.append('</g></svg>')
    return '\n'.join(o)

def readme_line(visitors):
    follow, star = f'https://github.com/{OWNER}', f'https://github.com/{OWNER}/{OWNER}'
    how = f'<a href="{follow}">follow</a> or <a href="{star}">⭐ star</a>'
    if not visitors:
        return f'<p align="center"><sub>The city is dark. {how} to light the first window</sub></p>'
    names = ', '.join(f'<a href="https://github.com/{v}">@{v}</a>' for v in reversed(visitors[-5:]))
    more = f' and {len(visitors) - 5} more' if len(visitors) > 5 else ''
    n = len(visitors)
    return f'<p align="center"><sub>{n} window{"s" if n != 1 else ""} lit by {names}{more} · {how} to light yours</sub></p>'

def main():
    if os.environ.get('LIGHTS_OFFLINE'):
        visitors = load()
    else:
        try:
            visitors = sync()
        except Exception as e:  # keep the city as it is rather than breaking it
            print(f'GitHub API failed, leaving the city unchanged: {e}', file=sys.stderr)
            return
    with open(os.path.join(REPO, 'assets', 'lights.svg'), 'w') as f:
        f.write(build(visitors))
    readme = os.path.join(REPO, 'README.md')
    s = open(readme).read()
    s = re.sub(r'(<!-- LIGHTS:START -->\n)(?:.*?\n)?(<!-- LIGHTS:END -->)',
               lambda m: m.group(1) + readme_line(visitors) + '\n' + m.group(2), s, flags=re.S)
    with open(readme, 'w') as f:
        f.write(s)
    print(len(visitors), 'lit windows')

if __name__ == '__main__':
    main()
