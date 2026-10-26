#!/usr/bin/env python3
"""Issue başlığına göre doğru oyuna yönlendirir. Girdi yalnızca ortam değişkenlerinden okunur."""
import os
import sys

import boss
import chess_game
from common import write_reply


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        boss.init_assets()
        chess_game.init_assets()
        return

    title = os.environ.get("ISSUE_TITLE", "").strip()
    user = os.environ.get("ISSUE_USER", "").strip()
    low = title.lower()
    if low.startswith("boss:"):
        if low.replace(" ", "") != "boss:attack":
            write_reply("❌ Başlık `boss: attack` olmalı. README'deki SALDIR! linkini kullan.")
            return
        boss.handle(user)
    elif low.startswith("chess:"):
        chess_game.handle(title, user)
    else:
        write_reply("Bu issue bir oyun komutu değil.")


if __name__ == "__main__":
    main()
