"""Builds assets/stats/activity.svg and assets/stats/languages.svg.

Same look as the project cards. Data comes from the GitHub GraphQL API (public
repositories and contributions only). Runs daily from .github/workflows/stats.yml.

Env:
  GITHUB_TOKEN   token for the GraphQL API (required unless STATS_DEMO is set)
  STATS_USER     GitHub user (default: ardacey)
  STATS_DEMO     render with made-up numbers, for local previews
"""
import json, os, random, sys, urllib.request
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', 'banner'))
from generate import text_path, text_width  # noqa: E402  (shared fonts + text-to-path)

USER = os.environ.get('STATS_USER', 'ardacey')
# notebooks are counted by raw file size (outputs, images), which drowns everything else
EXCLUDED_LANGUAGES = {'Jupyter Notebook'}
COLORS = ['#5ee7f2', '#ff5fa2', '#b18cff', '#ffa45c', '#7aa2f7']
OTHER = '#4a5070'
W, H, PAD = 400, 190, 22

# ---------- data ----------
QUERY = '''query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
  }
}'''

# commits in a date window, per repository (windows stay under 100 days, so no paging)
REPO_COMMITS = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      commitContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner }
        contributions(first: 100) { nodes { occurredAt commitCount } }
      }
    }
  }
}'''

def graphql(query, **variables):
    body = json.dumps({'query': query, 'variables': {'login': USER, **variables}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body, headers={
        'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if 'errors' in data:
        raise RuntimeError(data['errors'])
    return data['data']['user']

def automated_commits(first, last):
    """Commits to this profile repo per day. The daily workflows commit here as the
    owner, which would otherwise show up as an endless streak."""
    profile = f'{USER}/{USER}'.lower()
    counts, start = {}, first
    while start <= last:
        end = min(start + timedelta(days=89), last)
        coll = graphql(REPO_COMMITS, **{'from': f'{start}T00:00:00Z', 'to': f'{end}T23:59:59Z'})['contributionsCollection']
        for repo in coll['commitContributionsByRepository']:
            if repo['repository']['nameWithOwner'].lower() == profile:
                for n in repo['contributions']['nodes']:
                    day = date.fromisoformat(n['occurredAt'][:10])
                    counts[day] = counts.get(day, 0) + n['commitCount']
        start = end + timedelta(days=1)
    return counts

def fetch():
    user = graphql(QUERY)
    cal = user['contributionsCollection']['contributionCalendar']
    days = [(date.fromisoformat(d['date']), d['contributionCount'])
            for w in cal['weeks'] for d in w['contributionDays']]
    auto = automated_commits(days[0][0], days[-1][0])
    days = [(d, max(0, c - auto.get(d, 0))) for d, c in days]
    sizes = {}
    for repo in user['repositories']['nodes']:
        for e in repo['languages']['edges']:
            sizes[e['node']['name']] = sizes.get(e['node']['name'], 0) + e['size']
    return sum(c for _, c in days), days, sizes

def demo():
    random.seed(3)
    today = date.today()
    days = [(today - timedelta(days=i), random.choice([0, 0, 1, 2, 3, 5, 8])) for i in range(364, -1, -1)]
    sizes = {'Python': 380, 'Java': 220, 'TypeScript': 150, 'Kotlin': 100, 'JavaScript': 80, 'CSS': 40, 'Shell': 30}
    return sum(c for _, c in days), days, sizes

def streaks(days):
    """(current, longest) streak in days; today without contributions doesn't break the current one."""
    longest = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current = 0
    for i, (_, c) in enumerate(reversed(days)):
        if c:
            current += 1
        elif i > 0:
            break
    return current, longest

# ---------- drawing ----------
def frame():
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '<defs><linearGradient id="top" x1="0" x2="1">'
            '<stop offset="0" stop-color="#5ee7f2" stop-opacity="0.9"/>'
            '<stop offset="0.55" stop-color="#ff5fa2" stop-opacity="0.35"/>'
            '<stop offset="1" stop-color="#ff5fa2" stop-opacity="0"/></linearGradient></defs>',
            f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="#11131d" stroke="#2a2f45"/>',
            f'<rect x="{PAD}" y="0.5" width="{W - 2*PAD}" height="1.5" fill="url(#top)"/>']

def label(o, s, x, y, color='#8b93b8', size=10.5, anchor='start'):
    if anchor == 'end':
        x -= text_width(s, 'mono', size)
    o.append(f'<path d="{text_path(s, "mono", size, x, y)}" fill="{color}"/>')

def activity_card(total, days):
    current, longest = streaks(days)
    o = frame()
    label(o, 'ACTIVITY', PAD, 30, '#5ee7f2', 11)
    label(o, 'last 12 months', W - PAD, 30, anchor='end')
    o.append(f'<path d="{text_path(f"{total:,}", "light", 40, PAD, 82)}" fill="#f4f6ff"/>')
    label(o, 'contributions', PAD, 102)
    for i, (value, name) in enumerate(((current, 'current streak'), (longest, 'longest streak'))):
        x = 230 + i * 86
        o.append(f'<path d="{text_path(f"{value}d", "light", 22, x, 74)}" fill="#e6e9f5"/>')
        label(o, name.split()[0], x, 92, size=9.5)
        label(o, name.split()[1], x, 104, size=9.5)
    # weekly sparkline
    weeks = [sum(c for _, c in days[i:i + 7]) for i in range(max(0, len(days) - 364), len(days), 7)]
    peak = max(weeks) or 1
    bw = (W - 2 * PAD) / len(weeks)
    for i, v in enumerate(weeks):
        h = 3 + 42 * v / peak
        color = '#ff5fa2' if i == len(weeks) - 1 else '#5ee7f2'
        o.append(f'<rect x="{PAD + i * bw:.1f}" y="{168 - h:.1f}" width="{bw - 1.6:.1f}" height="{h:.1f}" rx="1" '
                 f'fill="{color}" fill-opacity="{0.25 + 0.6 * v / peak:.2f}"/>')
    o.append('</svg>')
    return '\n'.join(o)

def languages_card(sizes):
    sizes = {k: v for k, v in sizes.items() if k not in EXCLUDED_LANGUAGES and v > 0}
    total = sum(sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    top = ranked[:5]
    rest = sum(v for _, v in ranked[5:])
    rows = [(n, v, c) for (n, v), c in zip(top, COLORS)]
    if rest:
        rows.append(('Other', rest, OTHER))
    o = frame()
    label(o, 'LANGUAGES', PAD, 30, '#5ee7f2', 11)
    label(o, 'public repos', W - PAD, 30, anchor='end')
    # stacked bar
    x, bar_w = PAD, W - 2 * PAD
    o.append(f'<clipPath id="bar"><rect x="{PAD}" y="48" width="{bar_w}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">')
    for name, v, color in rows:
        w = bar_w * v / total
        o.append(f'<rect x="{x:.1f}" y="48" width="{w + 0.5:.1f}" height="8" fill="{color}"/>')
        x += w
    o.append('</g>')
    # legend, two columns
    for i, (name, v, color) in enumerate(rows):
        col, row = i % 2, i // 2
        x0, y0 = PAD + col * 184, 90 + row * 32
        o.append(f'<circle cx="{x0 + 4}" cy="{y0 - 5}" r="4" fill="{color}"/>')
        o.append(f'<path d="{text_path(name, "light", 15, x0 + 16, y0)}" fill="#e6e9f5"/>')
        label(o, f'{100 * v / total:.1f}%', x0 + 172, y0, anchor='end')
    o.append('</svg>')
    return '\n'.join(o)

def main():
    if os.environ.get('STATS_DEMO'):
        total, days, sizes = demo()
    else:
        try:
            total, days, sizes = fetch()
        except Exception as e:  # keep yesterday's cards rather than breaking the README
            print(f'GitHub API failed, leaving the stats unchanged: {e}', file=sys.stderr)
            return
    out = os.path.join(REPO, 'assets', 'stats')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'activity.svg'), 'w') as f:
        f.write(activity_card(total, days))
    with open(os.path.join(out, 'languages.svg'), 'w') as f:
        f.write(languages_card(sizes))
    print('total', total, 'streaks', streaks(days), 'languages', sorted(sizes, key=lambda k: -sizes[k])[:6])

if __name__ == '__main__':
    main()
