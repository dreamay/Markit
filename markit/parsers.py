"""浏览器书签解析（Chrome/Edge/Firefox/Safari/HTML）。"""

import glob
import json
import os
import platform
import plistlib
import shutil
import sqlite3
import tempfile
from html.parser import HTMLParser
from pathlib import Path


class BookmarkHTMLParser(HTMLParser):
    """浏览器书签 HTML 解析器（兼容 Chrome / Firefox 导出格式）。"""

    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self._current_href = None
        self._current_title = ""
        self._in_a = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs_dict = dict(attrs)
            self._current_href = attrs_dict.get("href", "")
            self._current_title = ""
            self._in_a = True

    def handle_data(self, data):
        if self._in_a:
            self._current_title += data

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_a:
            self._in_a = False
            if self._current_href and self._current_href.startswith("http"):
                self.bookmarks.append({
                    "title": self._current_title.strip(),
                    "url": self._current_href.strip(),
                })


def load_bookmarks(path: str) -> list[dict]:
    """加载书签，支持 .json 和浏览器导出的 .html 格式。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8")

    if p.suffix.lower() == ".json":
        return json.loads(text)

    # 当作浏览器导出的 HTML 解析
    parser = BookmarkHTMLParser()
    parser.feed(text)
    return parser.bookmarks


# ============================================================
# 自动从浏览器读取书签（macOS / Linux / Windows）
# ============================================================
def _get_home() -> Path:
    return Path.home()


def _find_chrome_bookmarks() -> list[Path]:
    """查找 Chrome 书签文件。"""
    home = _get_home()
    candidates = []
    if platform.system() == "Darwin":
        candidates = [
            home / "Library/Application Support/Google/Chrome/Default/Bookmarks",
            home / "Library/Application Support/Google/Chrome/Profile */Bookmarks",
        ]
    elif platform.system() == "Linux":
        candidates = [
            home / ".config/google-chrome/Default/Bookmarks",
            home / ".config/google-chrome/Profile */Bookmarks",
        ]
    elif platform.system() == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        candidates = [
            local / "Google/Chrome/User Data/Default/Bookmarks",
            local / "Google/Chrome/User Data/Profile */Bookmarks",
        ]
    results = []
    for c in candidates:
        results.extend(Path(p) for p in glob.glob(str(c)) if Path(p).is_file())
    return results


def _find_edge_bookmarks() -> list[Path]:
    """查找 Edge 书签文件。"""
    home = _get_home()
    candidates = []
    if platform.system() == "Darwin":
        candidates = [
            home / "Library/Application Support/Microsoft Edge/Default/Bookmarks",
            home / "Library/Application Support/Microsoft Edge/Profile */Bookmarks",
        ]
    elif platform.system() == "Linux":
        candidates = [
            home / ".config/microsoft-edge/Default/Bookmarks",
        ]
    elif platform.system() == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        candidates = [
            local / "Microsoft/Edge/User Data/Default/Bookmarks",
        ]
    results = []
    for c in candidates:
        results.extend(Path(p) for p in glob.glob(str(c)) if Path(p).is_file())
    return results


def _parse_chromium_bookmarks(path: Path) -> list[dict]:
    """解析 Chromium 系（Chrome/Edge）的 Bookmarks JSON 文件。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    bookmarks = []

    def walk(node, folder_path=""):
        if node.get("type") == "url":
            url = node.get("url", "")
            if url.startswith("http"):
                bookmarks.append({
                    "title": node.get("name", ""),
                    "url": url,
                    "folder": folder_path,
                })
        if node.get("type") == "folder":
            name = node.get("name", "")
            child_path = f"{folder_path}/{name}" if folder_path else name
            for child in node.get("children", []):
                walk(child, child_path)
        elif node.get("type") != "url":
            for child in node.get("children", []):
                walk(child, folder_path)

    for root_key in ("bookmark_bar", "other", "synced"):
        root = data.get("roots", {}).get(root_key)
        if root:
            walk(root)
    return bookmarks


def _find_firefox_places() -> list[Path]:
    """查找 Firefox 的 places.sqlite。"""
    home = _get_home()
    if platform.system() == "Darwin":
        pattern = str(home / "Library/Application Support/Firefox/Profiles/*/places.sqlite")
    elif platform.system() == "Linux":
        pattern = str(home / ".mozilla/firefox/*/places.sqlite")
    elif platform.system() == "Windows":
        appdata = Path(os.environ.get("APPDATA", ""))
        pattern = str(appdata / "Mozilla/Firefox/Profiles/*/places.sqlite")
    else:
        return []
    return [Path(p) for p in glob.glob(pattern) if Path(p).is_file()]


def _parse_firefox_bookmarks(places_path: Path) -> list[dict]:
    """从 Firefox places.sqlite 读取书签（复制后读取，避免锁冲突）。"""
    bookmarks = []
    tmp = tempfile.mktemp(suffix=".sqlite")
    try:
        shutil.copy2(str(places_path), tmp)
        conn = sqlite3.connect(tmp)
        cursor = conn.execute("""
            SELECT b.title, p.url, parent.title
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            LEFT JOIN moz_bookmarks parent ON b.parent = parent.id
            WHERE b.type = 1 AND p.url LIKE 'http%'
        """)
        for title, url, folder in cursor:
            bookmarks.append({
                "title": title or "",
                "url": url,
                "folder": folder or "",
            })
        conn.close()
    finally:
        Path(tmp).unlink(missing_ok=True)
    return bookmarks


def _find_safari_bookmarks() -> list[Path]:
    """查找 Safari 书签 plist（仅 macOS）。"""
    if platform.system() != "Darwin":
        return []
    p = _get_home() / "Library/Safari/Bookmarks.plist"
    return [p] if p.is_file() else []


def _parse_safari_bookmarks(plist_path: Path) -> list[dict]:
    """解析 Safari 的 Bookmarks.plist（binary plist）。"""
    bookmarks = []

    with open(plist_path, "rb") as f:
        data = plistlib.load(f)

    def walk(node, folder_path=""):
        if isinstance(node, dict):
            if node.get("URLString", "").startswith("http"):
                title = node.get("URIDictionary", {}).get("title", "")
                bookmarks.append({
                    "title": title,
                    "url": node["URLString"],
                    "folder": folder_path,
                })
            if "Children" in node:
                child_folder = folder_path
                if node.get("Title"):
                    child_folder = f"{folder_path}/{node['Title']}" if folder_path else node["Title"]
                for child in node["Children"]:
                    walk(child, child_folder)
        elif isinstance(node, list):
            for item in node:
                walk(item, folder_path)

    walk(data)
    return bookmarks


# 浏览器检测注册表：(名称, 查找函数, 解析函数)
BROWSER_READERS = [
    ("Chrome",  _find_chrome_bookmarks,  _parse_chromium_bookmarks),
    ("Edge",    _find_edge_bookmarks,    _parse_chromium_bookmarks),
    ("Firefox", _find_firefox_places,    _parse_firefox_bookmarks),
    ("Safari",  _find_safari_bookmarks,  _parse_safari_bookmarks),
]


def auto_detect_bookmarks() -> list[dict]:
    """自动检测并读取所有已安装浏览器的书签，去重后返回。"""
    all_bookmarks = []
    seen_urls = set()

    for name, finder, parser in BROWSER_READERS:
        paths = finder()
        for p in paths:
            try:
                items = parser(p)
                new_count = 0
                for bm in items:
                    if bm["url"] not in seen_urls:
                        seen_urls.add(bm["url"])
                        bm["browser"] = name
                        all_bookmarks.append(bm)
                        new_count += 1
                print(f"  [{name}] {p.name}: 读取 {len(items)} 个，新增 {new_count} 个")
            except Exception as e:
                print(f"  [{name}] {p}: 读取失败 ({e})")

    return all_bookmarks
