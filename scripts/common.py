"""Ortak yardimcilar: JSON durum dosyalari, README bolum guncelleme, ortam degiskenleri."""
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"


def repo() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "ardacey/ardacey")


def owner() -> str:
    return repo().split("/")[0]


def branch() -> str:
    return os.environ.get("DEFAULT_BRANCH", "main")


def raw_url(rel_path: str, bust: int = 0) -> str:
    """README'de gorselin onbellege takilmamasi icin ?v= ile mutlak raw URL."""
    return f"https://raw.githubusercontent.com/{repo()}/{branch()}/{rel_path}?v={bust}"


def load_json(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_section(text: str, name: str, content: str) -> str:
    pattern = re.compile(
        rf"(<!--START_SECTION:{name}-->)(.*?)(<!--END_SECTION:{name}-->)", re.S
    )
    if not pattern.search(text):
        raise SystemExit(f"README'de <!--START_SECTION:{name}--> isaretleri bulunamadi")
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)


def update_readme(name: str, content: str) -> None:
    readme = ROOT / "README.md"
    readme.write_text(
        replace_section(readme.read_text(encoding="utf-8"), name, content),
        encoding="utf-8",
    )


def write_reply(text: str) -> None:
    """Issue'ya yorum olarak atilacak metni dosyaya yazar."""
    path = os.environ.get("REPLY_FILE")
    if path:
        pathlib.Path(path).write_text(text, encoding="utf-8")
    else:
        print("--- REPLY ---\n" + text)


def new_issue_url(title: str, body: str = "") -> str:
    from urllib.parse import quote

    body = body or "Sadece asagidaki 'Create' / 'Submit new issue' butonuna bas. Gerisini bot halleder."
    return f"https://github.com/{repo()}/issues/new?title={quote(title)}&body={quote(body)}"
