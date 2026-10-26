"""README satrancı: herkes sırası gelen tarafın hamlesini 'chess: e2e4' başlıklı issue ile oynar."""
import re
import time
from datetime import date

import chess
import chess.pgn
import chess.svg

from common import (
    ASSETS, DATA, ROOT, load_json, new_issue_url, owner, raw_url, save_json,
    update_readme, write_reply,
)

STATE = DATA / "chess.json"
MOVE_RE = re.compile(r"^chess:\s*([a-h][1-8][a-h][1-8][qrbn]?)\s*$", re.I)


def default_state() -> dict:
    return {"moves": [], "players": {}, "last_mover": None, "history": [], "games_played": 0, "last_result": None}


def board_from(state: dict) -> chess.Board:
    board = chess.Board()
    for uci in state["moves"]:
        board.push_uci(uci)
    return board


def render_board(board: chess.Board, state: dict) -> None:
    last = chess.Move.from_uci(state["moves"][-1]) if state["moves"] else None
    sakura = {
        "square light": "#ffeaf3", "square dark": "#d98fb8",
        "square light lastmove": "#fff3a8", "square dark lastmove": "#f3d96b",
        "margin": "#3a1c5a", "coord": "#ffd1e8",
        "inner border": "#3a1c5a", "outer border": "#b388ff",
    }
    svg = chess.svg.board(board, lastmove=last, size=400, coordinates=True, colors=sakura)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "chess.svg").write_text(svg, encoding="utf-8")


def render_readme(board: chess.Board, state: dict) -> str:
    turn = "⚪ Beyaz" if board.turn == chess.WHITE else "⚫ Siyah"
    lines = [
        f'<p align="center"><img src="{raw_url("assets/chess.svg", int(time.time()))}" width="400" alt="Satranç tahtası"/></p>',
        "",
        f"**Sıra: {turn}** · Oynanan hamle: {len(state['moves'])} · Biten oyun: {state['games_played']}",
    ]
    if state["last_result"]:
        lines.append(f"\n_Önceki oyun: {state['last_result']}_")
    lines.append("")

    # Legal hamleler: kaynak kareye göre gruplanmış linkler
    by_from: dict[str, list[chess.Move]] = {}
    for mv in board.legal_moves:
        by_from.setdefault(chess.square_name(mv.from_square), []).append(mv)
    lines += [f"<details><summary><b>♟️ Hamle yap ({board.legal_moves.count()} legal hamle)</b></summary>", "",
              "Bir hamleye tıkla → açılan issue'da **Create**'e bas.", "",
              "| Taş | Gidebileceği kareler |", "|---|---|"]
    for sq in sorted(by_from):
        piece = board.piece_at(chess.parse_square(sq))
        sym = piece.unicode_symbol() if piece else ""
        links = []
        for mv in by_from[sq]:
            label = chess.square_name(mv.to_square) + (f"={chess.piece_symbol(mv.promotion).upper()}" if mv.promotion else "")
            links.append(f"[{label}]({new_issue_url('chess: ' + mv.uci())})")
        lines.append(f"| {sym} {sq} | " + " · ".join(links) + " |")
    lines += ["", "</details>", ""]

    if state["history"]:
        lines += ["**Son hamleler**", "", "| Hamle | Oyuncu |", "|---|---|"]
        for h in state["history"][:5]:
            lines.append(f'| {h["san"]} | @{h["user"]} |')
        lines.append("")
    top = sorted(state["players"].items(), key=lambda kv: -kv[1])[:5]
    if top:
        lines += ["**En aktif oyuncular**", "", "| # | Oyuncu | Hamle |", "|---|---|---|"]
        for i, (u, n) in enumerate(top, 1):
            lines.append(f"| {i} | @{u} | {n} |")
    return "\n".join(lines)


def archive_game(board: chess.Board, state: dict) -> str:
    game = chess.pgn.Game.from_board(board)
    game.headers["Event"] = "README Satrancı"
    game.headers["Date"] = date.today().isoformat()
    game.headers["Result"] = board.result()
    out = ROOT / "games"
    out.mkdir(exist_ok=True)
    n = state["games_played"] + 1
    (out / f"game-{n:04d}.pgn").write_text(str(game) + "\n", encoding="utf-8")
    if board.is_checkmate():
        who = "Siyah" if board.turn == chess.WHITE else "Beyaz"
        return f"{who} mat etti ({board.result()})"
    return f"Berabere ({board.result()})"


def refresh(board: chess.Board, state: dict) -> None:
    render_board(board, state)
    update_readme("chess", render_readme(board, state))


def handle(title: str, user: str) -> None:
    state = load_json(STATE, default_state())
    board = board_from(state)
    m = MOVE_RE.match(title.strip())
    if not m:
        write_reply("❌ Başlık `chess: e2e4` biçiminde olmalı. Hamle linklerini README'den kullan.")
        return
    uci = m.group(1).lower()
    move = chess.Move.from_uci(uci)
    if move not in board.legal_moves:
        write_reply(f"❌ `{uci}` şu an legal bir hamle değil (ya da sıra değişti). README'yi yenileyip tekrar dene.")
        return
    if state["last_mover"] == user and user.lower() != owner().lower():
        write_reply("⏳ Üst üste iki hamle yapamazsın; rakibin hamlesini bekle (ya da bir arkadaşını çağır).")
        return

    san = board.san(move)
    board.push(move)
    state["moves"].append(uci)
    state["last_mover"] = user
    state["players"][user] = state["players"].get(user, 0) + 1
    state["history"].insert(0, {"san": san, "user": user})
    state["history"] = state["history"][:10]
    reply = f"♟️ @{user} **{san}** oynadı."

    if board.is_game_over():
        summary = archive_game(board, state)
        state["games_played"] += 1
        state["last_result"] = summary
        reply += f"\n\n🏁 **Oyun bitti:** {summary}. Yeni oyun başlatıldı!"
        state["moves"], state["last_mover"] = [], None
        board = chess.Board()
    else:
        turn = "Beyaz" if board.turn == chess.WHITE else "Siyah"
        reply += f" Sıra {turn}'da." + (" ⚠️ Şah!" if board.is_check() else "")

    save_json(STATE, state)
    refresh(board, state)
    write_reply(reply)


def init_assets() -> None:
    state = load_json(STATE, default_state())
    save_json(STATE, state)
    refresh(board_from(state), state)
