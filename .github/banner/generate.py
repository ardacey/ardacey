"""Builds assets/banner.svg and assets/banner-mobile.svg.

The banner is a rainy Tokyo street scene with subtle CSS animations (rain, neon
flicker, text fade-in) and a "currently building" line taken from the owner's
public GitHub activity. Runs daily from .github/workflows/banner.yml.

Env:
  GITHUB_TOKEN   token for the GitHub API (optional, raises the rate limit)
  BANNER_USER    GitHub user (default: ardacey)
  LIVE_LABEL / LIVE_NAME   skip the API and use these values (for local testing)
"""
import base64, io, json, os, random, sys, urllib.request
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, 'scene.webp')
FONTS = {
    'light': os.path.join(HERE, 'fonts', 'InterDisplay-Light.otf'),
    'mono': os.path.join(HERE, 'fonts', 'JetBrainsMono-Regular.ttf'),
}
USER = os.environ.get('BANNER_USER', 'ardacey')

# ---------- text -> SVG paths (renders the same on every machine) ----------
_cache = {}

def font(name):
    if name not in _cache:
        f = TTFont(FONTS[name])
        _cache[name] = (f.getGlyphSet(), f.getBestCmap(), f['head'].unitsPerEm)
    return _cache[name]

def glyph(name, c):
    gs, cmap, _ = font(name)
    return gs[cmap.get(ord(c), cmap[ord('?')])]

def text_width(s, fname, size, tracking=0.0):
    upm = font(fname)[2]
    return sum(glyph(fname, c).width * size / upm + tracking * size for c in s)

def text_path(s, fname, size, x, y, tracking=0.0):
    gs, _, upm = font(fname)
    k = size / upm
    d = []
    for c in s:
        g = glyph(fname, c)
        pen = SVGPathPen(gs)
        g.draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
        d.append(pen.getCommands())
        x += g.width * k + tracking * size
    return ' '.join(d)

def fit(s, fname, size, max_w):
    """Shorten with an ellipsis until the text fits max_w."""
    if text_width(s, fname, size) <= max_w:
        return s
    while s and text_width(s + '…', fname, size) > max_w:
        s = s[:-1]
    return s.rstrip() + '…'

# ---------- live line: what am I working on? ----------
def api(path):
    req = urllib.request.Request('https://api.github.com' + path, headers={'Accept': 'application/vnd.github+json'})
    if os.environ.get('GITHUB_TOKEN'):
        req.add_header('Authorization', 'Bearer ' + os.environ['GITHUB_TOKEN'])
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def pretty(repo_name):
    return repo_name.replace('-', ' ').replace('_', ' ').strip()

def live_line():
    """(label, project) from public activity only; private repos never show up."""
    if os.environ.get('LIVE_NAME'):
        return os.environ.get('LIVE_LABEL', 'currently building'), os.environ['LIVE_NAME']
    now = datetime.now(timezone.utc)
    repos = [r for r in api(f'/users/{USER}/repos?type=owner&sort=pushed&per_page=50')
             if not r['fork'] and not r['archived'] and not r['private']
             and r['name'].lower() != USER.lower()]
    if not repos:
        return None
    eligible = {r['full_name']: r for r in repos}
    # most pushes in the last 7 days wins; ties go to the most recent push
    pushes = {}
    for ev in api(f'/users/{USER}/events/public?per_page=100'):
        when = datetime.fromisoformat(ev['created_at'].replace('Z', '+00:00'))
        if ev['type'] == 'PushEvent' and ev['repo']['name'] in eligible and now - when <= timedelta(days=7):
            pushes[ev['repo']['name']] = pushes.get(ev['repo']['name'], 0) + 1
    if pushes:
        top = max(pushes, key=lambda n: (pushes[n], eligible[n]['pushed_at']))
        return 'currently building', pretty(eligible[top]['name'])
    latest = repos[0]  # already sorted by pushed_at
    pushed = datetime.fromisoformat(latest['pushed_at'].replace('Z', '+00:00'))
    label = 'currently building' if now - pushed <= timedelta(days=30) else 'latest project'
    return label, pretty(latest['name'])

# ---------- scene ----------
CROP = (0, 12, 1024, 442)
W, H = CROP[2] - CROP[0], CROP[3] - CROP[1]

def scene():
    return Image.open(SRC).convert('RGB').crop(CROP)

def scene_b64():
    buf = io.BytesIO()
    scene().save(buf, 'JPEG', quality=88, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()

# neon signs (generous boxes in crop coords) that occasionally flicker.
# The flicker overlay is built from the sign's own pixels, so it lines up exactly.
SIGNS = [
    ((136, 0, 196, 104), '3.7s', '0.4s'),   # purple vertical sign
    ((472, 0, 532, 120), '5.3s', '1.6s'),   # orange vertical sign
    ((408, 98, 446, 202), '4.4s', '2.9s'),  # cyan vertical sign
]

def sign_overlay(box):
    """Dimmed copy of the sign, masked to its bright neon pixels."""
    im = scene().crop(box)
    h, sat, val = im.convert('HSV').split()
    # neon = bright AND saturated; haze around the signs is bright but grey-blue
    v = val.point(lambda x: max(0, min(255, (x - 120) * 3)))
    sm = sat.point(lambda x: max(0, min(255, (x - 70) * 3)))
    mask = ImageChops.multiply(v, sm)
    # white glyphs are unsaturated but very bright: keep them too
    mask = ImageChops.lighter(mask, val.point(lambda x: 255 if x > 225 else 0))
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    # fade out towards the box edges so no rectangle can show
    edge = Image.new('L', im.size, 0)
    ImageDraw.Draw(edge).rectangle((3, 3, im.width - 4, im.height - 4), fill=255)
    mask = ImageChops.multiply(mask, edge.filter(ImageFilter.GaussianBlur(2.5)))
    dim = im.point(lambda v: int(v * 0.28))
    dim.putalpha(mask)
    buf = io.BytesIO()
    dim.save(buf, 'PNG', optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

def rain_layer(n, speed, length, opacity, width, seed):
    random.seed(seed)
    lines = []
    for _ in range(n):
        x = random.uniform(-40, W)
        y = random.uniform(0, H)
        for dy in (0, -H):  # second copy one tile above for seamless loop
            lines.append(f'M{x:.1f},{y+dy:.1f} l{-length*0.12:.1f},{length:.1f}')
    return (f'<g class="rain" style="animation-duration:{speed}" opacity="{opacity}">'
            f'<path d="{" ".join(lines)}" stroke="#d6ecff" stroke-width="{width}" stroke-linecap="round"/></g>')

def build(mobile=False, live=None):
    """mobile: bigger text and thicker rain, for a ~360px wide phone screen.
    live: optional (label, name) shown under the tagline."""
    rw = 2.2 if mobile else 1.0
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    o.append(f'''<style>
  .rain {{ animation: fall linear infinite; }}
  @keyframes fall {{ from {{ transform: translateY(0); }} to {{ transform: translateY({H}px); }} }}
  .flicker {{ animation: flick ease-in-out infinite; opacity: 0; }}
  @keyframes flick {{ 0%,86%,100% {{ opacity: 0; }} 88% {{ opacity: .75; }} 90% {{ opacity: .1; }} 92% {{ opacity: .6; }} 95% {{ opacity: 0; }} }}
  .fade {{ animation: rise 1.6s ease-out both; }}
  .d1 {{ animation-delay: .3s; }} .d2 {{ animation-delay: .6s; }} .d3 {{ animation-delay: .9s; }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  .pulse {{ animation: pulse 2.4s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
  @keyframes pulse {{ 0% {{ transform: scale(1); opacity: .7; }} 70%,100% {{ transform: scale(3.2); opacity: 0; }} }}
</style>
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  <radialGradient id="scrim" cx="{820 if mobile else 770}" cy="{215 if mobile else 225}" r="{310 if mobile else 240}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#05060d" stop-opacity="{0.72 if mobile else 0.62}"/>
    <stop offset="1" stop-color="#05060d" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="vignette" cx="0.5" cy="0.5" r="0.75">
    <stop offset="0.6" stop-color="#000" stop-opacity="0"/>
    <stop offset="1" stop-color="#000" stop-opacity="0.45"/>
  </radialGradient>
</defs>
<g clip-path="url(#frame)">''')
    o.append(f'<image width="{W}" height="{H}" href="data:image/jpeg;base64,{scene_b64()}"/>')
    for (x0, y0, x1, y1), dur, delay in SIGNS:
        o.append(f'<image class="flicker" style="animation-duration:{dur};animation-delay:{delay}" '
                 f'x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" href="data:image/png;base64,{sign_overlay((x0, y0, x1, y1))}"/>')
    o.append(rain_layer(70, '1.6s', 26, 0.22, 0.8 * rw, 1))
    o.append(rain_layer(45, '1.0s', 40, 0.30, 1.1 * rw, 2))
    o.append(f'<rect width="{W}" height="{H}" fill="#1b2140" opacity="0.12"/>')  # unify colour grade
    o.append(f'<rect width="{W}" height="{H}" fill="url(#scrim)"/>')
    o.append(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>')

    # text block
    right = W - 24
    if mobile:
        tx = 640
        o.append(f'<g class="fade"><rect x="{tx}" y="110" width="60" height="3" fill="#5ee7f2"/></g>')
        o.append(f'<g class="fade d1"><path d="{text_path("Software", "light", 46, tx, 172)}" fill="#e6e9f5" fill-opacity="0.95"/>'
                 f'<path d="{text_path("Engineer", "light", 46, tx, 222)}" fill="#e6e9f5" fill-opacity="0.95"/></g>')
        o.append(f'<g class="fade d2"><path d="{text_path("AI agents / mobile", "mono", 22, tx, 264)}" fill="#8fd9e6" fill-opacity="0.9"/>'
                 f'<path d="{text_path("full-stack", "mono", 22, tx, 294)}" fill="#8fd9e6" fill-opacity="0.9"/></g>')
        if live:
            label, name = live
            o.append(f'<g class="fade d3"><circle class="pulse" cx="{tx + 7}" cy="335" r="6" fill="#5ee7f2"/>'
                     f'<circle cx="{tx + 7}" cy="335" r="6" fill="#5ee7f2"/>'
                     f'<path d="{text_path(label, "mono", 20, tx + 24, 342)}" fill="#8b93b8"/>'
                     f'<path d="{text_path(fit(name, "light", 30, right - tx), "light", 30, tx, 382)}" fill="#e6e9f5" fill-opacity="0.95"/></g>')
    else:
        tx = 690
        o.append(f'<g class="fade"><rect x="{tx}" y="188" width="32" height="1.5" fill="#5ee7f2"/></g>')
        o.append(f'<g class="fade d1"><path d="{text_path("Software Engineer", "light", 20, tx, 222)}" fill="#e6e9f5" fill-opacity="0.92"/></g>')
        o.append(f'<g class="fade d2"><path d="{text_path("AI agents  /  mobile  /  full-stack", "mono", 11, tx, 252)}" fill="#8fd9e6" fill-opacity="0.8"/></g>')
        if live:
            label, name = live
            lx = tx + 13
            nx = lx + text_width(label + '  ', 'mono', 10.5)
            if text_width(name, 'light', 14) <= right - nx:
                name_at = (name, nx, 287)
            else:  # long project name: own line under the label
                name_at = (fit(name, 'light', 14, right - lx), lx, 307)
            o.append(f'<g class="fade d3"><circle class="pulse" cx="{tx + 3}" cy="282" r="3" fill="#5ee7f2"/>'
                     f'<circle cx="{tx + 3}" cy="282" r="3" fill="#5ee7f2"/>'
                     f'<path d="{text_path(label, "mono", 10.5, lx, 286)}" fill="#8b93b8"/>'
                     f'<path d="{text_path(name_at[0], "light", 14, name_at[1], name_at[2])}" fill="#e6e9f5" fill-opacity="0.92"/></g>')
    o.append('</g></svg>')
    return '\n'.join(o)

def main():
    try:
        live = live_line()
    except Exception as e:  # keep yesterday's banner rather than dropping the line
        print(f'GitHub API failed, leaving the banner unchanged: {e}', file=sys.stderr)
        return
    print('live line:', live)
    for name, mobile in (('banner.svg', False), ('banner-mobile.svg', True)):
        with open(os.path.join(REPO, 'assets', name), 'w') as f:
            f.write(build(mobile, live))

if __name__ == '__main__':
    main()
