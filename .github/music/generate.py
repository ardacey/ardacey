"""Builds assets/music.svg: a small "last played" pill fed by Last.fm
(Spotify scrobbles there). Runs hourly from .github/workflows/music.yml.

Text is drawn by the viewer's browser (not converted to paths) so song titles
in any script, Japanese included, render properly.

Env:
  LASTFM_API_KEY  Last.fm API key (repository secret)
  LASTFM_USER     Last.fm user (default: ardacey)
  MUSIC_DEMO      "title|artist" to render without calling the API
"""
import base64, json, os, sys, urllib.parse, urllib.request
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
USER = os.environ.get('LASTFM_USER', 'ardacey')
W, H = 460, 52
PLACEHOLDER = '2a96cbd8b46e442fc41c2b86b821562f'
FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, 'Hiragino Sans', 'Noto Sans JP', 'Yu Gothic', sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

def get(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()

def last_track():
    """(title, artist, cover_url or None) of the most recent scrobble."""
    q = urllib.parse.urlencode({'method': 'user.getrecenttracks', 'user': USER, 'limit': 1,
                                'api_key': os.environ['LASTFM_API_KEY'], 'format': 'json'})
    tracks = json.loads(get('https://ws.audioscrobbler.com/2.0/?' + q))['recenttracks']['track']
    if not tracks:
        return None
    t = tracks[0] if isinstance(tracks, list) else tracks
    images = {i['size']: i['#text'] for i in t.get('image', []) if i.get('#text')}
    cover = images.get('medium') or images.get('small')
    if cover and PLACEHOLDER in cover:  # Last.fm's grey star when there is no artwork
        cover = None
    return t['name'], t['artist']['#text'], cover

def cover_b64(url):
    try:
        data = get(url)
    except Exception:
        return None
    mime = 'image/png' if data[:4] == b'\x89PNG' else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(data).decode()

def est_width(s, size=14):
    """Rough rendered width: wide (CJK) characters take a full em, others about half."""
    return sum(size if ord(c) > 0x2E80 else size * 0.56 for c in s)

def clip(s, max_w):
    if est_width(s) <= max_w:
        return s
    while s and est_width(s + '…') > max_w:
        s = s[:-1]
    return s.rstrip() + '…'

def build(title, artist, cover=None):
    x = 58 if cover else 50
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    o.append('''<style>
  .eq { animation: eq 1.1s ease-in-out infinite alternate; transform-box: fill-box; transform-origin: bottom; }
  @keyframes eq { from { transform: scaleY(.25); } to { transform: scaleY(1); } }
</style>''')
    o.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="{H/2 - 0.5}" fill="#11131d" stroke="#2a2f45"/>')
    if cover:
        o.append(f'<clipPath id="c"><rect x="10" y="10" width="32" height="32" rx="6"/></clipPath>'
                 f'<image x="10" y="10" width="32" height="32" clip-path="url(#c)" href="{cover}"/>')
    else:
        o.append('<circle cx="26" cy="26" r="13" fill="#171a28" stroke="#2f3550"/>'
                 '<circle cx="26" cy="26" r="2.5" fill="#5ee7f2"/>')
    o.append(f'<text x="{x}" y="21" font-family="{MONO}" font-size="10" fill="#8b93b8">last played</text>')
    room = W - x - 58  # leave the equalizer free
    artist = clip(artist, room * 0.4)
    title = clip(title, room - est_width('  ·  ' + artist))
    o.append(f'<text x="{x}" y="39" font-family="{FONT}" font-size="14" fill="#e6e9f5">{escape(title)}'
             f'<tspan fill="#8b93b8">  ·  {escape(artist)}</tspan></text>')
    # little equalizer on the right
    for i, (h, d) in enumerate(((14, 0), (20, .35), (10, .7))):
        o.append(f'<rect class="eq" style="animation-delay:{d}s" x="{W - 40 + i * 7}" y="{34 - h}" width="4" height="{h}" rx="1.5" fill="#5ee7f2" opacity="{0.9 - i * 0.15:.2f}"/>')
    o.append('</svg>')
    return '\n'.join(o)

def main():
    if os.environ.get('MUSIC_DEMO'):
        title, artist = os.environ['MUSIC_DEMO'].split('|')
        track = (title, artist, None)
    elif not os.environ.get('LASTFM_API_KEY'):
        print('LASTFM_API_KEY is not set, skipping', file=sys.stderr)
        return
    else:
        try:
            track = last_track()
        except Exception as e:  # keep the last song rather than breaking the README
            print(f'Last.fm failed, leaving the pill unchanged: {e}', file=sys.stderr)
            return
        if not track:
            return
    title, artist, cover_url = track
    svg = build(title, artist, cover_b64(cover_url) if cover_url else None)
    with open(os.path.join(REPO, 'assets', 'music.svg'), 'w') as f:
        f.write(svg)
    print('last played:', title, '-', artist)

if __name__ == '__main__':
    main()
