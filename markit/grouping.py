"""分类逻辑（keyword/folder/browser 三种分组函数）。"""

from .config import CATEGORY_RULES


def classify(url: str, rules: dict[str, list[str]] | None = None) -> str:
    """根据 URL 匹配分类规则，未匹配的归入"其他"。"""
    if rules is None:
        rules = CATEGORY_RULES
    lower = url.lower()
    for category, keywords in rules.items():
        for kw in keywords:
            if kw in lower:
                return category
    return "其他"


def group_bookmarks(bookmarks: list[dict], rules: dict[str, list[str]] | None = None) -> dict[str, list[dict]]:
    """将书签按关键词分类分组，并在每组内按 title 排序。"""
    groups: dict[str, list[dict]] = {}
    for bm in bookmarks:
        cat = classify(bm["url"], rules)
        groups.setdefault(cat, []).append(bm)
    for v in groups.values():
        v.sort(key=lambda b: b["title"].lower())
    # 按分类名排序，"其他"放最后
    return dict(sorted(groups.items(), key=lambda kv: (kv[0] == "其他", kv[0])))


def group_by_folder(bookmarks: list[dict]) -> dict[str, list[dict]]:
    """按书签文件夹分组。优先取第二级文件夹（跳过 bookmark_bar 等根节点名）。"""
    groups: dict[str, list[dict]] = {}
    for bm in bookmarks:
        folder = bm.get("folder", "").strip("/")
        if not folder:
            cat = "其他"
        else:
            parts = folder.split("/")
            # 路径有多级时取第二级（跳过"收藏夹栏"等根名），否则取第一级
            cat = parts[1] if len(parts) > 1 else parts[0]
        groups.setdefault(cat, []).append(bm)
    for v in groups.values():
        v.sort(key=lambda b: b["title"].lower())
    return dict(sorted(groups.items(), key=lambda kv: (kv[0] == "其他", kv[0])))


def group_by_browser(bookmarks: list[dict]) -> dict[str, list[dict]]:
    """按来源浏览器分组。"""
    groups: dict[str, list[dict]] = {}
    for bm in bookmarks:
        browser = bm.get("browser", "其他")
        groups.setdefault(browser, []).append(bm)
    for v in groups.values():
        v.sort(key=lambda b: b["title"].lower())
    return dict(sorted(groups.items(), key=lambda kv: kv[0]))
