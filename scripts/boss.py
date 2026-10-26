"""Boss fight: ziyaretci 'boss: attack' basligiyla issue acar, bot hasar uygular."""
import random
import time
from xml.sax.saxutils import escape

from anime import FONT, burst, demon, petals, sparkles, speed_lines
from common import ASSETS, DATA, load_json, new_issue_url, raw_url, save_json, update_readme, write_reply

STATE = DATA / "boss.json"

BOSSES = [
    ("Bug Golem", "#a1887f", "#ffd54f"),
    ("Merge Conflict Hydrası", "#66bb6a", "#ffeb3b"),
    ("Legacy Code Lich", "#9575cd", "#80deea"),
    ("Null Pointer Hayaleti", "#90a4ae", "#ff80ab"),
    ("Sonsuz Döngü Yılanı", "#ef5350", "#ffd180"),
    ("Segfault Ejderhası", "#ff8a65", "#fff59d"),
]


def max_hp_for(defeated: int) -> int:
    return 500 + 150 * defeated


def default_state() -> dict:
    return {
        "boss_index": 0, "defeated": 0, "max_hp": max_hp_for(0), "hp": max_hp_for(0),
        "damage": {}, "recent": [], "hall": [], "hits": 0,
    }


def para(x, y, w, h, dx=12):
    return f"{x + dx},{y} {x + w + dx},{y} {x + w},{y + h} {x},{y + h}"


def render_svg(state: dict) -> str:
    name, body, accent = BOSSES[state["boss_index"] % len(BOSSES)]
    W, H = 640, 250
    hp, mx = max(state["hp"], 0), state["max_hp"]
    frac = hp / mx
    hp_c1, hp_c2 = ("#7cf08c", "#00c853") if frac > 0.5 else ("#ffd54f", "#ff9800") if frac > 0.2 else ("#ff8a80", "#ff1744")
    last = state["recent"][0] if state["recent"] else None
    pop = ""
    if last:
        crit = last.get("crit")
        pop = (
            burst(250, 66, 52, 34, 14, "#fff176" if not crit else "#ff5252", "#ff6f00" if not crit else "#ffffff", rot=0.2)
            + f'<text x="250" y="{74 if not crit else 68}" font-size="{26 if not crit else 24}" font-weight="bold" font-style="italic" '
              f'fill="{"#d84315" if not crit else "#ffffff"}" text-anchor="middle">-{last["dmg"]}</text>'
            + ('<text x="250" y="84" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">CRITICAL!</text>' if crit else "")
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" role="img" aria-label="Boss: {escape(name)}">'
        '<defs>'
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2a0a3a"/>'
        '<stop offset="0.6" stop-color="#6a1b4d"/><stop offset="1" stop-color="#ff5e62"/></linearGradient>'
        '<linearGradient id="fr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd1e8"/><stop offset="1" stop-color="#b388ff"/></linearGradient>'
        f'<linearGradient id="hp" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{hp_c1}"/><stop offset="1" stop-color="{hp_c2}"/></linearGradient>'
        f'<clipPath id="clip"><rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="18"/></clipPath>'
        '</defs>'
        '<g clip-path="url(#clip)">'
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
        + speed_lines(120, 125, W, H, 40, seed=11, opacity=0.10)
        + sparkles(W, H, 16, seed=4, color="#ffe3f1")
        + petals(W, H, 10, seed=8)
        + '<g><animateTransform attributeName="transform" type="translate" values="0,0;0,-6;0,0" dur="2.6s" repeatCount="indefinite"/>'
        + demon(14, 14, 0.98, body, accent, state["boss_index"], "d")
        + "</g>"
        + pop
        # sağ panel
        + f'<text x="262" y="124" fill="none" font-size="25" font-weight="bold" font-style="italic" stroke="#3a0b3f" stroke-width="6" stroke-linejoin="round">{escape(name)}</text>'
        + f'<text x="262" y="124" fill="#ffffff" font-size="25" font-weight="bold" font-style="italic">{escape(name)}</text>'
        + f'<rect x="262" y="136" width="88" height="22" rx="11" fill="{accent}"/>'
        + f'<text x="306" y="151" fill="#2b0a3a" font-size="12" font-weight="bold" text-anchor="middle">STAGE {state["defeated"] + 1}</text>'
        + f'<text x="360" y="151" fill="#ffe3f1" font-size="12">Yenilen boss: {state["defeated"]} · Toplam vuruş: {state["hits"]}</text>'
        + f'<polygon points="{para(256, 172, 360, 24, 12)}" fill="#12041c" stroke="#ffffff" stroke-width="2.5" stroke-linejoin="round"/>'
        + (f'<polygon points="{para(258, 174, 356 * frac, 20, 11)}" fill="url(#hp)"/>' if frac > 0 else "")
        + f'<text x="440" y="190" fill="#ffffff" font-size="13" font-weight="bold" font-style="italic" text-anchor="middle">{hp} / {mx} HP</text>'
        + f'<text x="262" y="218" fill="#ffd1e8" font-size="11">Saldır linkine tıkla ve hasarını README\'ye yaz!</text>'
        + '</g>'
        f'<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="18" fill="none" stroke="url(#fr)" stroke-width="3"/>'
        "</svg>"
    )


def render_readme(state: dict) -> str:
    name = BOSSES[state["boss_index"] % len(BOSSES)][0]
    board = sorted(state["damage"].items(), key=lambda kv: -kv[1])[:5]
    lines = [
        f'<p align="center"><img src="{raw_url("assets/boss.svg", int(time.time()))}" width="640" alt="{escape(name)}"/></p>',
        "",
        f'<p align="center"><a href="{new_issue_url("boss: attack")}"><b>⚔️ SALDIR!</b></a> '
        "· linke tıkla → açılan issue'da <i>Create</i>'e bas → birkaç saniye içinde hasarın README'ye yansır</p>",
        "",
    ]
    if state["recent"]:
        lines += ["**Son vuruşlar**", "", "| Oyuncu | Hasar |", "|---|---|"]
        for r in state["recent"][:5]:
            crit = " 💥 KRİTİK" if r.get("crit") else ""
            lines.append(f'| @{r["user"]} | {r["dmg"]}{crit} |')
        lines.append("")
    if board:
        lines += ["**En çok hasar verenler**", "", "| # | Oyuncu | Toplam |", "|---|---|---|"]
        for i, (u, d) in enumerate(board, 1):
            lines.append(f"| {i} | @{u} | {d} |")
        lines.append("")
    if state["hall"]:
        slain = ", ".join(f'{h["boss"]} (@{h["slayer"]})' for h in state["hall"][-3:][::-1])
        lines.append(f"🏆 **Son yenilenler:** {slain}")
    return "\n".join(lines)


def attack(state: dict, user: str, rng=random) -> str:
    dmg = rng.randint(10, 30)
    crit = rng.random() < 0.10
    if crit:
        dmg *= 2
    state["hp"] -= dmg
    state["hits"] += 1
    state["damage"][user] = state["damage"].get(user, 0) + dmg
    state["recent"].insert(0, {"user": user, "dmg": dmg, "crit": crit})
    state["recent"] = state["recent"][:10]
    name = BOSSES[state["boss_index"] % len(BOSSES)][0]
    msg = f"⚔️ @{user}, **{name}**'e **{dmg}** hasar verdin{' (💥 KRİTİK!)' if crit else ''}."
    if state["hp"] <= 0:
        state["defeated"] += 1
        state["hall"].append({"boss": name, "slayer": user})
        state["boss_index"] += 1
        state["max_hp"] = max_hp_for(state["defeated"])
        state["hp"] = state["max_hp"]
        nxt = BOSSES[state["boss_index"] % len(BOSSES)][0]
        msg += f"\n\n🏆 **{name} yenildi!** Son vuruş sende, @{user}. Yeni rakip: **{nxt}** ({state['max_hp']} HP)."
    else:
        msg += f" Kalan can: {state['hp']}/{state['max_hp']}"
    return msg


def handle(user: str) -> None:
    state = load_json(STATE, default_state())
    reply = attack(state, user)
    save_json(STATE, state)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "boss.svg").write_text(render_svg(state), encoding="utf-8")
    update_readme("boss", render_readme(state))
    write_reply(reply)


def init_assets() -> None:
    """İlk kurulumda boss.svg ve README bölümünü üretir."""
    state = load_json(STATE, default_state())
    save_json(STATE, state)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "boss.svg").write_text(render_svg(state), encoding="utf-8")
    update_readme("boss", render_readme(state))
