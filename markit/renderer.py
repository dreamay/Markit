"""HTML 生成（支持多模式前端切换）。"""

import json
from pathlib import Path
from urllib.parse import urlparse


def favicon_url(url: str) -> str:
    """用 Google favicon 服务获取网站图标。"""
    domain = urlparse(url).netloc
    return f"https://www.google.com/s2/favicons?sz=32&domain={domain}"


def _escape(text: str) -> str:
    """HTML 转义。"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def generate_html(all_groups: dict[str, dict[str, list[dict]]], output: str = "index.html"):
    """生成静态 HTML 文件，包含三种分类视图，前端切换。"""
    from .config import CATEGORY_RULES

    seen_urls = set()
    all_bookmarks = []
    url_to_cats = {}

    for mode, groups in all_groups.items():
        for cat, items in groups.items():
            for bm in items:
                url = bm["url"]
                if url not in url_to_cats:
                    url_to_cats[url] = {}
                url_to_cats[url][mode] = cat
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_bookmarks.append(bm)

    total = len(all_bookmarks)

    cards_html = ""
    for bm in all_bookmarks:
        te = _escape(bm["title"])
        ue = _escape(bm["url"])
        domain = urlparse(bm["url"]).netloc
        cats = url_to_cats.get(bm["url"], {})
        cf = _escape(cats.get("folder", "其他"))
        ck = _escape(cats.get("keyword", "其他"))
        cb = _escape(cats.get("browser", "其他"))
        fc = te[0] if te else "?"
        cards_html += (
            f'\n      <a class="card" href="{ue}" target="_blank" rel="noopener"'
            f' data-cat-folder="{cf}" data-cat-keyword="{ck}" data-cat-browser="{cb}"'
            f' data-search="{te.lower()} {domain.lower()}" data-url="{ue}" data-title="{te}">'
            f'<img class="favicon" src="{favicon_url(bm["url"])}" alt="" loading="lazy"'
            f""" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><rect width=%2232%22 height=%2232%22 rx=%226%22 fill=%22%234f46e5%22/><text x=%2216%22 y=%2222%22 text-anchor=%22middle%22 fill=%22white%22 font-size=%2218%22>{fc}</text></svg>'">"""
            f'<div class="info"><div class="title">{te}</div>'
            f'<div class="domain">{domain}</div></div></a>'
        )

    categories_data = {}
    for mode, groups in all_groups.items():
        categories_data[mode] = list(groups.keys())
    categories_json = json.dumps(categories_data, ensure_ascii=False)
    mode_labels_json = json.dumps({"home": "主页", "folder": "文件夹", "keyword": "关键词", "browser": "浏览器"}, ensure_ascii=False)
    rules_json = json.dumps(CATEGORY_RULES, ensure_ascii=False)

    # ---- 构建 HTML ----
    # 用列表拼接避免 f-string 里大量 {{ }}
    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MarkIt - 我的书签</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><rect width=%2232%22 height=%2232%22 rx=%228%22 fill=%22%236366f1%22/><text x=%2216%22 y=%2223%22 text-anchor=%22middle%22 fill=%22white%22 font-size=%2220%22 font-weight=%22bold%22>M</text></svg>">
""")
    # CSS
    parts.append("""<style>
  :root {
    --bg: #1a2236; --surface: #243049; --surface2: #3a4a6b;
    --text: #f1f5f9; --text2: #94a3b8; --accent: #6366f1;
    --accent2: #818cf8; --radius: 12px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh;
    background-size: cover; background-position: center; background-attachment: fixed;
  }
  .header { text-align: center; padding: 48px 20px 16px; position: relative; }
  .header h1 {
    font-size: 2rem; font-weight: 700;
    background: linear-gradient(135deg, var(--accent), #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .subtitle { color: var(--text2); font-size: 0.85rem; margin-top: 4px; }
  .header .stats { color: var(--text2); margin-top: 8px; font-size: 0.95rem; }
  .top-bar {
    position: absolute; top: 20px; right: 20px;
    display: flex; align-items: center; gap: 8px;
  }
  .mode-switcher {
    display: flex; gap: 4px; background: var(--surface);
    border-radius: 8px; padding: 4px; border: 1px solid var(--surface2);
  }
  .mode-btn {
    padding: 6px 14px; border-radius: 6px; font-size: 0.85rem;
    border: none; background: transparent;
    color: var(--text2); cursor: pointer; transition: all .2s; white-space: nowrap;
  }
  .mode-btn:hover { color: var(--accent2); }
  .mode-btn.active { background: var(--accent); color: #fff; }
  .icon-btn {
    width: 36px; height: 36px; border-radius: 8px; border: 1px solid var(--surface2);
    background: var(--surface); color: var(--text2); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all .2s; font-size: 18px; line-height: 1;
  }
  .icon-btn:hover { border-color: var(--accent2); color: var(--accent2); }
  .modal-overlay {
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5);
    z-index: 100; align-items: center; justify-content: center; backdrop-filter: blur(4px);
  }
  .modal-overlay.open { display: flex; }
  .modal {
    background: var(--surface); border: 1px solid var(--surface2);
    border-radius: 16px; padding: 28px; width: 460px; max-width: 90vw;
    max-height: 80vh; overflow-y: auto;
  }
  .modal h2 { font-size: 1.15rem; font-weight: 600; margin-bottom: 20px; color: var(--text); }
  .modal label { display: block; font-size: 0.85rem; color: var(--text2); margin-bottom: 6px; }
  .modal input[type="text"], .modal select {
    width: 100%; padding: 10px 12px; font-size: 0.9rem;
    border: 1px solid var(--surface2); border-radius: 8px;
    background: var(--bg); color: var(--text); outline: none; transition: border-color .2s;
  }
  .modal input[type="text"]:focus, .modal select:focus { border-color: var(--accent); }
  .modal input[type="text"]::placeholder { color: var(--text2); }
  .modal-field { margin-bottom: 16px; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
  .modal-actions button {
    padding: 8px 20px; border-radius: 8px; font-size: 0.85rem;
    cursor: pointer; border: none; transition: all .2s;
  }
  .btn-cancel { background: var(--surface2); color: var(--text2); }
  .btn-cancel:hover { color: var(--text); }
  .btn-save { background: var(--accent); color: #fff; }
  .btn-save:hover { background: var(--accent2); }
  .toolbar { max-width: 900px; margin: 0 auto 12px; padding: 0 20px; display: flex; flex-direction: column; gap: 12px; }
  .toolbar-row { display: flex; gap: 10px; align-items: center; }
  .search-box {
    flex: 1; padding: 12px 16px; font-size: 1rem;
    border: 1px solid var(--surface2); border-radius: var(--radius);
    background: var(--surface); color: var(--text); outline: none; transition: border-color .2s;
  }
  .search-box:focus { border-color: var(--accent); }
  .search-box::placeholder { color: var(--text2); }
  .sort-select {
    padding: 10px 12px; font-size: 0.85rem; border-radius: var(--radius);
    border: 1px solid var(--surface2); background: var(--surface); color: var(--text2);
    outline: none; cursor: pointer;
  }
  .view-toggle { display: flex; border-radius: 8px; overflow: hidden; border: 1px solid var(--surface2); }
  .view-btn {
    padding: 8px 10px; border: none; background: var(--surface); color: var(--text2);
    cursor: pointer; transition: all .2s; display: flex; align-items: center;
  }
  .view-btn.active { background: var(--accent); color: #fff; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; align-items: center; padding: 4px 0; }
  .tag {
    padding: 5px 12px; border-radius: 20px; font-size: 0.82rem;
    border: 1px solid var(--surface2); background: transparent;
    color: var(--text2); cursor: pointer; transition: all .2s; position: relative;
  }
  .tag:hover { border-color: var(--accent2); color: var(--accent2); }
  .tag.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .tag .del-cat {
    display: inline-block; width: 14px; height: 14px; line-height: 14px;
    text-align: center; font-size: 10px; border-radius: 50%;
    margin-left: 4px; vertical-align: middle;
    opacity: 0; transition: opacity .15s; cursor: pointer;
    background: rgba(255,255,255,.15);
  }
  .tag:hover .del-cat { opacity: .6; }
  .tag .del-cat:hover { opacity: 1; background: #dc2626; color: #fff; }
  .grid {
    max-width: 900px; margin: 0 auto; padding: 0 20px 60px;
    display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px;
  }
  .grid.list-view { grid-template-columns: 1fr; }
  .grid.list-view .card { gap: 10px; padding: 10px 14px; }
  .grid.list-view .favicon { width: 20px; height: 20px; }
  .grid.list-view .title { font-size: 0.9rem; }
  .grid.list-view .domain { display: inline; margin-left: 8px; }
  .grid.list-view .info { display: flex; align-items: center; }
  .grid.list-view .visit-count { font-size: 0.75rem; }
  .card {
    display: flex; align-items: center; gap: 12px; position: relative;
    padding: 14px 16px; border-radius: var(--radius);
    background: var(--surface); text-decoration: none; color: var(--text);
    border: 1px solid transparent; transition: all .2s;
  }
  .card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 20px rgba(99,102,241,.15); }
  .card.hidden { display: none; }
  .card.dup-highlight { border-color: #f59e0b; }
  .favicon { width: 32px; height: 32px; border-radius: 6px; flex-shrink: 0; }
  .info { overflow: hidden; flex: 1; }
  .title { font-size: 0.95rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .domain { font-size: 0.8rem; color: var(--text2); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .visit-count { font-size: 0.7rem; color: var(--text2); margin-top: 2px; }
  .card-actions { position: absolute; top: 6px; right: 6px; display: none; gap: 2px; }
  .card:hover .card-actions { display: flex; }
  .card-action {
    width: 24px; height: 24px; border-radius: 4px; border: none;
    background: var(--surface2); color: var(--text2); cursor: pointer;
    display: flex; align-items: center; justify-content: center; font-size: 12px; transition: all .15s;
  }
  .card-action:hover { background: var(--accent); color: #fff; }
  .empty { grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text2); font-size: 1.1rem; }
  .settings-section { border-top: 1px solid var(--surface2); margin-top: 20px; padding-top: 16px; }
  .settings-section h3 { font-size: 0.9rem; font-weight: 500; color: var(--text2); margin-bottom: 12px; }
  .settings-row { display: flex; gap: 10px; }
  .settings-row button {
    flex: 1; padding: 8px 0; border-radius: 8px; font-size: 0.85rem;
    cursor: pointer; border: 1px solid var(--surface2); transition: all .2s;
    background: var(--bg); color: var(--text2);
  }
  .settings-row button:hover { border-color: var(--accent2); color: var(--accent2); }
  .footer { text-align: center; padding: 20px; color: var(--text2); font-size: 0.8rem; }
  .footer a { color: var(--accent2); text-decoration: none; }
  .homepage { max-width: 900px; margin: 0 auto; padding: 0 20px 60px; display: none; }
  .homepage.active { display: block; }
  .home-section { margin-bottom: 28px; }
  .home-section-title {
    font-size: 0.95rem; font-weight: 600; color: var(--text2); margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
  }
  .home-section-title svg { opacity: .6; }
  .home-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px;
  }
  .home-empty { color: var(--text2); font-size: 0.85rem; padding: 16px 0; opacity: .6; }
  .card-action.pin-action.pinned { color: #f59e0b; }
  .card-action.pin-action.pinned:hover { background: #f59e0b; color: #fff; }
  .dup-banner {
    max-width: 900px; margin: 0 auto 12px; padding: 10px 20px;
    background: rgba(245,158,11,.15); border: 1px solid #f59e0b;
    border-radius: var(--radius); color: #fbbf24; font-size: 0.85rem;
    display: none; align-items: center; gap: 8px;
  }
  .dup-banner.show { display: flex; }
  .dup-banner button {
    margin-left: auto; padding: 4px 12px; border-radius: 6px; border: 1px solid #f59e0b;
    background: transparent; color: #fbbf24; cursor: pointer; font-size: 0.8rem;
  }
  body.light {
    --bg: #f0f2f5; --surface: #ffffff; --surface2: #d1d5db;
    --text: #1f2937; --text2: #6b7280; --accent: #6366f1; --accent2: #818cf8;
  }
  body.light .modal { background: #fff; border-color: #d1d5db; }
  body.light .modal input[type="text"], body.light .modal select { background: #f0f2f5; color: #1f2937; border-color: #d1d5db; }
  body.light .card { background: #fff; }
  body.light .card-action { background: #e5e7eb; color: #6b7280; }
  body.light .search-box, body.light .sort-select { background: #fff; color: #1f2937; border-color: #d1d5db; }
  body.light .dup-banner { background: rgba(245,158,11,.1); }
  @media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; }
    .header h1 { font-size: 1.5rem; }
    .top-bar { position: static; justify-content: center; margin: 16px auto 0; flex-wrap: wrap; }
  }
</style>
</head>
<body>
""")
    # Body HTML
    parts.append(f"""
<div class="header">
  <div class="top-bar">
    <div class="mode-switcher" id="modeSwitcher"></div>
    <button class="icon-btn" id="addBtn" title="添加书签">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
    </button>
    <button class="icon-btn" id="themeBtn" title="切换明暗模式">
      <svg id="themeIcon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
    <button class="icon-btn" id="settingsBtn" title="设置">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
    </button>
  </div>
  <h1>MarkIt</h1>
  <div class="subtitle">一款本地功能丰富的书签管理器</div>
  <p class="stats" id="stats">共 {total} 个书签</p>
</div>
""")
    # Modals - plain strings, no f-string needed
    parts.append("""
<div class="modal-overlay" id="settingsModal">
  <div class="modal">
    <h2>设置</h2>
    <div class="modal-field">
      <label for="bgInput">背景图片链接</label>
      <input type="text" id="bgInput" placeholder="输入图片 URL，留空则使用默认背景">
    </div>
    <div class="settings-section">
      <h3>自定义书签数据</h3>
      <div class="settings-row">
        <button id="exportBtn">导出 JSON</button>
        <button id="importBtn">导入 JSON</button>
      </div>
      <input type="file" id="importFile" accept=".json" style="display:none">
    </div>
    <div class="modal-actions">
      <button class="btn-cancel" id="settingsCancel">取消</button>
      <button class="btn-save" id="settingsSave">保存</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="bmModal">
  <div class="modal">
    <h2 id="bmModalTitle">添加书签</h2>
    <div class="modal-field">
      <label for="bmTitleInput">标题</label>
      <input type="text" id="bmTitleInput" placeholder="网站名称">
    </div>
    <div class="modal-field">
      <label for="bmUrlInput">URL</label>
      <input type="text" id="bmUrlInput" placeholder="https://example.com">
    </div>
    <div class="modal-field">
      <label for="bmCatSelect">分类</label>
      <select id="bmCatSelect"></select>
    </div>
    <div class="modal-actions">
      <button class="btn-cancel" id="bmCancel">取消</button>
      <button class="btn-save" id="bmSave">保存</button>
    </div>
  </div>
</div>

<div class="dup-banner" id="dupBanner">
  <span id="dupText"></span>
  <button id="dupDismiss">忽略</button>
</div>
""")
    # Toolbar + grid
    parts.append(f"""
<div class="toolbar">
  <div class="toolbar-row">
    <input class="search-box" type="text" placeholder="搜索书签... (按 / 聚焦)" id="search">
    <select class="sort-select" id="sortSelect">
      <option value="name">按名称</option>
      <option value="time">按时间</option>
      <option value="recent">最近使用</option>
      <option value="visits">访问次数</option>
    </select>
    <div class="view-toggle" id="viewToggle">
      <button class="view-btn active" data-view="card" title="卡片视图">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      </button>
      <button class="view-btn" data-view="list" title="列表视图">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="4" width="18" height="3" rx="1"/><rect x="3" y="10.5" width="18" height="3" rx="1"/><rect x="3" y="17" width="18" height="3" rx="1"/></svg>
      </button>
    </div>
  </div>
  <div class="tags" id="tags"></div>
</div>

<div class="grid" id="grid">
{cards_html}
</div>

<div class="homepage" id="homepage">
  <div class="home-section">
    <div class="home-section-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      常用书签
    </div>
    <div class="home-grid" id="homePinned"></div>
  </div>
  <div class="home-section">
    <div class="home-section-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      最近访问
    </div>
    <div class="home-grid" id="homeRecent"></div>
  </div>
  <div class="home-section">
    <div class="home-section-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
      访问最多
    </div>
    <div class="home-grid" id="homeTopVisits"></div>
  </div>
</div>

<div class="footer">Made by <a href="http://songit.cn/" target="_blank" rel="noopener">dreamsong</a></div>
""")
    # JS - plain string with placeholders, then replace
    js = """<script>
const CATEGORIES = __CATEGORIES__;
const MODE_LABELS = __MODE_LABELS__;
const RULES = __RULES__;
const MODES = ['home', ...Object.keys(CATEGORIES)];
const STORAGE_KEY = 'markit-custom-bookmarks';
const VISITS_KEY = 'markit-visits';
const RECENT_KEY = 'markit-recent';
const PINS_KEY = 'markit-pins';

const modeSwitcher = document.getElementById('modeSwitcher');
const tagsEl = document.getElementById('tags');
const gridEl = document.getElementById('grid');
const searchInput = document.getElementById('search');
const statsEl = document.getElementById('stats');
const staticTotal = __TOTAL__;

let currentMode = localStorage.getItem('markit-mode') || 'home';
if (!MODES.includes(currentMode)) currentMode = 'home';
let activeCat = 'all';
let currentSort = localStorage.getItem('markit-sort') || 'name';
let currentView = localStorage.getItem('markit-view') || 'card';

// ---- helpers ----
function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}
function classifyUrl(url) {
  const lower = url.toLowerCase();
  for (const [cat, keywords] of Object.entries(RULES)) {
    for (const kw of keywords) { if (lower.includes(kw)) return cat; }
  }
  return '其他';
}
function faviconSrc(url) {
  try { return 'https://www.google.com/s2/favicons?sz=32&domain=' + new URL(url).hostname; }
  catch { return ''; }
}
function domainOf(url) {
  try { return new URL(url).hostname; } catch { return ''; }
}

// ---- localStorage wrappers ----
function loadCustom() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; } catch { return []; }
}
function saveCustom(list) { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)); }
function getVisits() {
  try { return JSON.parse(localStorage.getItem(VISITS_KEY)) || {}; } catch { return {}; }
}
function addVisit(url) {
  const v = getVisits(); v[url] = (v[url] || 0) + 1;
  localStorage.setItem(VISITS_KEY, JSON.stringify(v));
  const r = getRecent(); r.unshift(url);
  const unique = [...new Set(r)].slice(0, 500);
  localStorage.setItem(RECENT_KEY, JSON.stringify(unique));
}
function getRecent() {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY)) || []; } catch { return []; }
}
function getPins() {
  try { return JSON.parse(localStorage.getItem(PINS_KEY)) || []; } catch { return []; }
}
function togglePin(url) {
  const pins = getPins();
  const idx = pins.indexOf(url);
  if (idx >= 0) pins.splice(idx, 1); else pins.push(url);
  localStorage.setItem(PINS_KEY, JSON.stringify(pins));
  return idx < 0;
}

// ---- custom cards ----
function renderCustomCards() {
  gridEl.querySelectorAll('.card.custom').forEach(el => el.remove());
  const customs = loadCustom();
  customs.forEach((bm, idx) => {
    const cat = bm.category || classifyUrl(bm.url);
    const domain = domainOf(bm.url);
    const t = bm.title || '';
    const first = t.charAt(0) || '?';
    const card = document.createElement('a');
    card.className = 'card custom';
    card.href = bm.url;
    card.target = '_blank';
    card.rel = 'noopener';
    card.draggable = true;
    card.setAttribute('data-cat-folder', bm.folder || '手动添加');
    card.setAttribute('data-cat-keyword', cat);
    card.setAttribute('data-cat-browser', bm.browser || '手动添加');
    card.setAttribute('data-custom-idx', idx);
    card.setAttribute('data-url', bm.url);
    card.setAttribute('data-title', t);
    card.dataset.search = (t + ' ' + domain).toLowerCase();
    const img = document.createElement('img');
    img.className = 'favicon'; img.src = faviconSrc(bm.url); img.alt = ''; img.loading = 'lazy';
    img.onerror = function() {
      this.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%234f46e5'/%3E%3Ctext x='16' y='22' text-anchor='middle' fill='white' font-size='18'%3E" + encodeURIComponent(first) + "%3C/text%3E%3C/svg%3E";
    };
    const info = document.createElement('div'); info.className = 'info';
    info.innerHTML = '<div class="title">' + escapeHtml(t) + '</div><div class="domain">' + escapeHtml(domain) + '</div><div class="visit-count"></div>';
    const actions = document.createElement('div'); actions.className = 'card-actions';
    const pins = getPins();
    const isPinned = pins.includes(bm.url);
    actions.innerHTML = '<button class="card-action pin-action' + (isPinned ? ' pinned' : '') + '" data-url="' + escapeHtml(bm.url) + '" title="' + (isPinned ? '取消收藏' : '收藏到主页') + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="' + (isPinned ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></button>'
      + '<button class="card-action edit-action" data-idx="' + idx + '" title="编辑">&#9998;</button>'
      + '<button class="card-action copy-action" data-url="' + escapeHtml(bm.url) + '" data-title="' + escapeHtml(t) + '" title="复制"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>'
      + '<button class="card-action del-action" data-idx="' + idx + '" title="删除">&times;</button>';
    card.appendChild(img); card.appendChild(info); card.appendChild(actions);
    gridEl.appendChild(card);
  });
}

// ---- add actions to static cards ----
function addStaticCardActions() {
  gridEl.querySelectorAll('.card:not(.custom)').forEach(card => {
    if (card.querySelector('.card-actions')) return;
    const url = card.getAttribute('data-url') || card.href;
    const title = card.getAttribute('data-title') || card.querySelector('.title')?.textContent || '';
    const actions = document.createElement('div'); actions.className = 'card-actions';
    const pinsS = getPins();
    const isPinnedS = pinsS.includes(url);
    actions.innerHTML = '<button class="card-action pin-action' + (isPinnedS ? ' pinned' : '') + '" data-url="' + escapeHtml(url) + '" title="' + (isPinnedS ? '取消收藏' : '收藏到主页') + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="' + (isPinnedS ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></button>'
      + '<button class="card-action edit-static" data-url="' + escapeHtml(url) + '" data-title="' + escapeHtml(title) + '" title="编辑">&#9998;</button>'
      + '<button class="card-action copy-action" data-url="' + escapeHtml(url) + '" data-title="' + escapeHtml(title) + '" title="复制"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>'
      + '<button class="card-action del-static" data-url="' + escapeHtml(url) + '" title="删除">&times;</button>';
    card.appendChild(actions);
  });
}

// ---- visit count display ----
function updateVisitCounts() {
  const visits = getVisits();
  gridEl.querySelectorAll('.card').forEach(card => {
    const url = card.getAttribute('data-url') || card.href;
    const vc = card.querySelector('.visit-count');
    const count = visits[url] || 0;
    if (vc) vc.textContent = count > 0 ? count + ' 次访问' : '';
    else if (count > 0) {
      const info = card.querySelector('.info');
      if (info) {
        const el = document.createElement('div'); el.className = 'visit-count';
        el.textContent = count + ' 次访问'; info.appendChild(el);
      }
    }
  });
}

// ---- click tracking ----
gridEl.addEventListener('click', e => {
  const card = e.target.closest('.card');
  if (!card) return;
  const action = e.target.closest('.card-action');
  if (action) {
    e.preventDefault(); e.stopPropagation();
    // pin to homepage
    if (action.classList.contains('pin-action')) {
      const pinUrl = action.dataset.url;
      const nowPinned = togglePin(pinUrl);
      action.classList.toggle('pinned', nowPinned);
      action.title = nowPinned ? '取消收藏' : '收藏到主页';
      const svg = action.querySelector('svg');
      if (svg) svg.setAttribute('fill', nowPinned ? 'currentColor' : 'none');
      if (currentMode === 'home') renderHomepage();
      return;
    }
    // edit custom
    if (action.classList.contains('edit-action')) {
      const idx = parseInt(action.dataset.idx);
      const customs = loadCustom();
      if (idx >= 0 && idx < customs.length) openBmModal(customs[idx], idx);
      return;
    }
    // delete custom
    if (action.classList.contains('del-action')) {
      const idx = parseInt(action.dataset.idx);
      const customs = loadCustom(); customs.splice(idx, 1); saveCustom(customs);
      renderCustomCards(); addStaticCardActions(); buildTags(); filter();
      return;
    }
    // copy
    if (action.classList.contains('copy-action')) {
      const url = action.dataset.url; const title = action.dataset.title;
      const text = title + ' - ' + url;
      navigator.clipboard.writeText(text).then(() => { const old = action.innerHTML; action.innerHTML = '&#10003;'; setTimeout(() => action.innerHTML = old, 1200); });
      return;
    }
    // edit static
    if (action.classList.contains('edit-static')) {
      openStaticEditModal(action.dataset.url, action.dataset.title, card);
      return;
    }
    // delete static (hide from page)
    if (action.classList.contains('del-static')) {
      if (!confirm('确定删除此书签？')) return;
      card.remove(); filter();
      return;
    }
    return;
  }
  // track visit
  const url = card.getAttribute('data-url') || card.href;
  if (url) addVisit(url);
});

// ---- categories ----
function collectCategories() {
  const cats = {};
  const dataModes = MODES.filter(m => m !== 'home');
  for (const m of dataModes) cats[m] = new Set(CATEGORIES[m] || []);
  const customs = loadCustom();
  customs.forEach(bm => {
    cats['folder'].add(bm.folder || '手动添加');
    cats['keyword'].add(bm.category || classifyUrl(bm.url));
    cats['browser'].add(bm.browser || '手动添加');
  });
  const result = {};
  for (const m of dataModes) {
    const arr = [...cats[m]];
    arr.sort((a, b) => { if (a === '其他') return 1; if (b === '其他') return -1; return a.localeCompare(b); });
    result[m] = arr;
  }
  return result;
}

// ---- mode switcher ----
MODES.forEach(mode => {
  const btn = document.createElement('button');
  btn.className = 'mode-btn' + (mode === currentMode ? ' active' : '');
  btn.dataset.mode = mode;
  if (mode === 'home') {
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg> 主页';
  } else {
    btn.textContent = MODE_LABELS[mode] || mode;
  }
  modeSwitcher.appendChild(btn);
});

// ---- tags ----
function buildTags() {
  tagsEl.innerHTML = '';
  const allBtn = document.createElement('button');
  allBtn.className = 'tag active'; allBtn.dataset.cat = 'all'; allBtn.textContent = '全部';
  tagsEl.appendChild(allBtn);
  const allCats = collectCategories();
  (allCats[currentMode] || []).forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'tag'; btn.dataset.cat = c;
    btn.innerHTML = escapeHtml(c) + '<span class="del-cat" data-cat="' + escapeHtml(c) + '" title="删除此分类">&times;</span>';
    tagsEl.appendChild(btn);
  });
  activeCat = 'all';
}

// ---- delete category ----
tagsEl.addEventListener('click', e => {
  const delCat = e.target.closest('.del-cat');
  if (delCat) {
    e.stopPropagation();
    const cat = delCat.dataset.cat;
    if (!confirm('确定删除分类「' + cat + '」下的所有自定义书签？\\n（浏览器导入的书签不受影响）')) return;
    const customs = loadCustom();
    const attr = 'data-cat-' + currentMode;
    const filtered = customs.filter(bm => {
      if (currentMode === 'keyword') return (bm.category || classifyUrl(bm.url)) !== cat;
      if (currentMode === 'folder') return (bm.folder || '手动添加') !== cat;
      return true;
    });
    saveCustom(filtered);
    renderCustomCards(); addStaticCardActions(); buildTags(); filter();
    return;
  }
  if (!e.target.classList.contains('tag')) return;
  tagsEl.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
  e.target.classList.add('active');
  activeCat = e.target.dataset.cat;
  filter();
});

// ---- sort & filter ----
function getAllCards() { return [...gridEl.querySelectorAll('.card')]; }

function sortCards() {
  const cards = getAllCards();
  const visits = getVisits();
  const recent = getRecent();
  if (currentSort === 'time') { cards.forEach(c => gridEl.appendChild(c)); return; }
  cards.sort((a, b) => {
    const urlA = a.getAttribute('data-url') || a.href;
    const urlB = b.getAttribute('data-url') || b.href;
    if (currentSort === 'visits') return (visits[urlB] || 0) - (visits[urlA] || 0);
    if (currentSort === 'recent') return (recent.indexOf(urlA) === -1 ? 9999 : recent.indexOf(urlA)) - (recent.indexOf(urlB) === -1 ? 9999 : recent.indexOf(urlB));
    const tA = (a.getAttribute('data-title') || '').toLowerCase();
    const tB = (b.getAttribute('data-title') || '').toLowerCase();
    return tA.localeCompare(tB);
  });
  cards.forEach(c => gridEl.appendChild(c));
}

function filter() {
  const q = searchInput.value.toLowerCase().trim();
  const attr = 'data-cat-' + currentMode;
  const cards = getAllCards();
  let visible = 0;
  cards.forEach(card => {
    const cardCat = card.getAttribute(attr) || '其他';
    const matchCat = activeCat === 'all' || cardCat === activeCat;
    const matchSearch = !q || card.dataset.search.includes(q);
    const show = matchCat && matchSearch;
    card.classList.toggle('hidden', !show);
    if (show) visible++;
  });
  const allCats = collectCategories();
  const catCount = (allCats[currentMode] || []).length;
  const totalCount = staticTotal + loadCustom().length;
  statsEl.textContent = '共 ' + totalCount + ' 个书签 · ' + catCount + ' 个分类 · ' + MODE_LABELS[currentMode] + '视图';
  let empty = document.getElementById('empty-msg');
  if (visible === 0) {
    if (!empty) { empty = document.createElement('div'); empty.id = 'empty-msg'; empty.className = 'empty'; empty.textContent = '没有找到匹配的书签'; gridEl.appendChild(empty); }
  } else if (empty) { empty.remove(); }
}

// ---- homepage ----
const homepageEl = document.getElementById('homepage');
const toolbarEl = document.querySelector('.toolbar');
const dupBannerEl = document.getElementById('dupBanner');

function getAllCardData() {
  const cards = [];
  gridEl.querySelectorAll('.card').forEach(card => {
    const url = card.getAttribute('data-url') || card.href;
    const title = card.getAttribute('data-title') || card.querySelector('.title')?.textContent || '';
    if (url) cards.push({ url, title });
  });
  return cards;
}

function createHomeCard(bm) {
  const domain = domainOf(bm.url);
  const t = bm.title || '';
  const first = t.charAt(0) || '?';
  const card = document.createElement('a');
  card.className = 'card';
  card.href = bm.url;
  card.target = '_blank';
  card.rel = 'noopener';
  card.setAttribute('data-url', bm.url);
  card.setAttribute('data-title', t);
  const img = document.createElement('img');
  img.className = 'favicon'; img.src = faviconSrc(bm.url); img.alt = ''; img.loading = 'lazy';
  img.onerror = function() {
    this.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%234f46e5'/%3E%3Ctext x='16' y='22' text-anchor='middle' fill='white' font-size='18'%3E" + encodeURIComponent(first) + "%3C/text%3E%3C/svg%3E";
  };
  const info = document.createElement('div'); info.className = 'info';
  const visits = getVisits();
  const count = visits[bm.url] || 0;
  info.innerHTML = '<div class="title">' + escapeHtml(t) + '</div><div class="domain">' + escapeHtml(domain) + '</div>' + (count > 0 ? '<div class="visit-count">' + count + ' 次访问</div>' : '');
  card.appendChild(img); card.appendChild(info);
  card.addEventListener('click', () => { addVisit(bm.url); });
  return card;
}

function renderHomepage() {
  const allCards = getAllCardData();
  const urlMap = {};
  allCards.forEach(c => { urlMap[c.url] = c; });
  // also include custom bookmarks
  const customs = loadCustom();
  customs.forEach(c => { if (!urlMap[c.url]) urlMap[c.url] = { url: c.url, title: c.title || c.url }; });

  // pinned
  const pinnedEl = document.getElementById('homePinned');
  pinnedEl.innerHTML = '';
  const pins = getPins();
  const pinnedItems = pins.map(url => urlMap[url]).filter(Boolean);
  if (pinnedItems.length === 0) {
    pinnedEl.innerHTML = '<div class="home-empty">点击书签上的 ★ 图标收藏到主页</div>';
  } else {
    pinnedItems.forEach(bm => pinnedEl.appendChild(createHomeCard(bm)));
  }

  // recent
  const recentEl = document.getElementById('homeRecent');
  recentEl.innerHTML = '';
  const recent = getRecent();
  const recentItems = recent.slice(0, 12).map(url => urlMap[url]).filter(Boolean);
  if (recentItems.length === 0) {
    recentEl.innerHTML = '<div class="home-empty">访问书签后会显示在这里</div>';
  } else {
    recentItems.forEach(bm => recentEl.appendChild(createHomeCard(bm)));
  }

  // top visits
  const topEl = document.getElementById('homeTopVisits');
  topEl.innerHTML = '';
  const visits = getVisits();
  const sorted = Object.entries(visits).sort((a, b) => b[1] - a[1]).slice(0, 12);
  const topItems = sorted.map(([url]) => urlMap[url]).filter(Boolean);
  if (topItems.length === 0) {
    topEl.innerHTML = '<div class="home-empty">访问书签后会显示在这里</div>';
  } else {
    topItems.forEach(bm => topEl.appendChild(createHomeCard(bm)));
  }
}

function switchMode(mode) {
  currentMode = mode; localStorage.setItem('markit-mode', mode);
  modeSwitcher.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  const isHome = mode === 'home';
  homepageEl.classList.toggle('active', isHome);
  gridEl.style.display = isHome ? 'none' : '';
  toolbarEl.style.display = isHome ? 'none' : '';
  if (dupBannerEl) dupBannerEl.style.display = isHome ? 'none' : '';
  if (isHome) {
    renderHomepage();
    const totalCount = staticTotal + loadCustom().length;
    statsEl.textContent = '共 ' + totalCount + ' 个书签 · 主页';
  } else {
    buildTags(); sortCards(); filter();
  }
}
modeSwitcher.addEventListener('click', e => {
  if (!e.target.classList.contains('mode-btn')) return;
  switchMode(e.target.dataset.mode);
});
searchInput.addEventListener('input', filter);
document.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement !== searchInput) { e.preventDefault(); searchInput.focus(); }
});

// ---- sort select ----
const sortSelect = document.getElementById('sortSelect');
sortSelect.value = currentSort;
sortSelect.addEventListener('change', () => {
  currentSort = sortSelect.value; localStorage.setItem('markit-sort', currentSort);
  sortCards(); filter();
});

// ---- view toggle ----
const viewToggle = document.getElementById('viewToggle');
function applyView() {
  gridEl.classList.toggle('list-view', currentView === 'list');
  viewToggle.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === currentView));
}
viewToggle.addEventListener('click', e => {
  const btn = e.target.closest('.view-btn'); if (!btn) return;
  currentView = btn.dataset.view; localStorage.setItem('markit-view', currentView);
  applyView();
});

// ---- add/edit bookmark modal ----
const addBtn = document.getElementById('addBtn');
const bmModal = document.getElementById('bmModal');
const bmModalTitle = document.getElementById('bmModalTitle');
const bmTitleInput = document.getElementById('bmTitleInput');
const bmUrlInput = document.getElementById('bmUrlInput');
const bmCatSelect = document.getElementById('bmCatSelect');
const bmSave = document.getElementById('bmSave');
const bmCancel = document.getElementById('bmCancel');
let editingIdx = -1;

function populateCatSelect(selected) {
  bmCatSelect.innerHTML = '';
  const allCats = collectCategories();
  const cats = allCats[currentMode] || [];
  cats.forEach(c => {
    const opt = document.createElement('option'); opt.value = c; opt.textContent = c;
    if (c === selected) opt.selected = true;
    bmCatSelect.appendChild(opt);
  });
  const optNew = document.createElement('option'); optNew.value = '__new__'; optNew.textContent = '+ 新建分类';
  bmCatSelect.appendChild(optNew);
}

function openBmModal(bm, idx) {
  bmModalTitle.textContent = idx >= 0 ? '编辑书签' : '添加书签';
  bmTitleInput.value = bm ? bm.title : '';
  bmUrlInput.value = bm ? bm.url : '';
  editingIdx = idx;
  const cat = bm ? (bm.category || classifyUrl(bm.url)) : '';
  populateCatSelect(cat);
  bmModal.classList.add('open');
  bmTitleInput.focus();
}
function closeBmModal() { bmModal.classList.remove('open'); editingIdx = -1; }
addBtn.addEventListener('click', () => openBmModal(null, -1));
bmCancel.addEventListener('click', closeBmModal);
bmModal.addEventListener('click', e => { if (e.target === bmModal) closeBmModal(); });

bmCatSelect.addEventListener('change', () => {
  if (bmCatSelect.value === '__new__') {
    const name = prompt('输入新分类名称：');
    if (name && name.trim()) {
      const opt = document.createElement('option'); opt.value = name.trim(); opt.textContent = name.trim();
      bmCatSelect.insertBefore(opt, bmCatSelect.lastChild);
      bmCatSelect.value = name.trim();
    } else { bmCatSelect.value = bmCatSelect.options[0]?.value || '其他'; }
  }
});

bmSave.addEventListener('click', () => {
  const title = bmTitleInput.value.trim();
  let url = bmUrlInput.value.trim();
  if (!url) return;
  if (!/^https?:\\/\\//.test(url)) url = 'https://' + url;
  let cat = bmCatSelect.value;
  if (cat === '__new__') cat = '其他';
  // dup check
  const customs = loadCustom();
  const allUrls = new Set();
  gridEl.querySelectorAll('.card:not(.custom)').forEach(c => allUrls.add(c.getAttribute('data-url') || c.href));
  customs.forEach((b, i) => { if (i !== editingIdx) allUrls.add(b.url); });
  if (allUrls.has(url)) { if (!confirm('该网址已存在，确定继续添加？')) return; }
  const entry = { title: title || url, url, category: cat };
  if (currentMode === 'folder') entry.folder = cat;
  if (editingIdx >= 0 && editingIdx < customs.length) { customs[editingIdx] = entry; }
  else { customs.push(entry); }
  saveCustom(customs);
  renderCustomCards(); addStaticCardActions(); buildTags(); sortCards(); filter(); updateVisitCounts();
  closeBmModal();
});

// ---- edit static bookmark (copy to custom, allow edit) ----
function openStaticEditModal(url, title, card) {
  const cats = {};
  MODES.forEach(m => { cats[m] = card.getAttribute('data-cat-' + m) || '其他'; });
  bmModalTitle.textContent = '编辑书签';
  bmTitleInput.value = title;
  bmUrlInput.value = url;
  editingIdx = -2; // special: static edit
  populateCatSelect(cats[currentMode]);
  bmModal.classList.add('open');
  bmModal._staticCard = card;
  bmTitleInput.focus();
}

// patch bmSave for static edit
const origBmSave = bmSave.onclick;
bmSave.addEventListener('click', () => {
  if (editingIdx !== -2) return; // handled by main handler above
  // For static cards: update DOM directly
  const card = bmModal._staticCard;
  if (!card) return;
  const title = bmTitleInput.value.trim();
  let cat = bmCatSelect.value;
  if (cat === '__new__') cat = '其他';
  if (title) {
    const titleEl = card.querySelector('.title');
    if (titleEl) titleEl.textContent = title;
    card.setAttribute('data-title', title);
    card.dataset.search = (title + ' ' + domainOf(card.href)).toLowerCase();
  }
  card.setAttribute('data-cat-' + currentMode, cat);
  closeBmModal();
  buildTags(); filter();
});

// ---- duplicate detection ----
function checkDuplicates() {
  const urlMap = {};
  gridEl.querySelectorAll('.card').forEach(card => {
    const url = card.getAttribute('data-url') || card.href;
    if (!url) return;
    card.classList.remove('dup-highlight');
    if (!urlMap[url]) urlMap[url] = [];
    urlMap[url].push(card);
  });
  let dupCount = 0;
  for (const [url, cards] of Object.entries(urlMap)) {
    if (cards.length > 1) { dupCount += cards.length; cards.forEach(c => c.classList.add('dup-highlight')); }
  }
  const banner = document.getElementById('dupBanner');
  const text = document.getElementById('dupText');
  if (dupCount > 0) {
    text.textContent = '检测到 ' + dupCount + ' 个重复网址';
    banner.classList.add('show');
  } else { banner.classList.remove('show'); }
}
document.getElementById('dupDismiss').addEventListener('click', () => {
  document.getElementById('dupBanner').classList.remove('show');
  gridEl.querySelectorAll('.dup-highlight').forEach(c => c.classList.remove('dup-highlight'));
});

// ---- settings ----
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const bgInput = document.getElementById('bgInput');
const settingsSave = document.getElementById('settingsSave');
const settingsCancel = document.getElementById('settingsCancel');
const exportBtn = document.getElementById('exportBtn');
const importBtn = document.getElementById('importBtn');
const importFile = document.getElementById('importFile');

function applyBg() {
  const url = localStorage.getItem('markit-bg') || '';
  document.body.style.backgroundImage = url ? 'url(' + url + ')' : 'none';
}
settingsBtn.addEventListener('click', () => {
  bgInput.value = localStorage.getItem('markit-bg') || '';
  settingsModal.classList.add('open');
});
settingsCancel.addEventListener('click', () => settingsModal.classList.remove('open'));
settingsModal.addEventListener('click', e => { if (e.target === settingsModal) settingsModal.classList.remove('open'); });
settingsSave.addEventListener('click', () => {
  const url = bgInput.value.trim();
  if (url) localStorage.setItem('markit-bg', url); else localStorage.removeItem('markit-bg');
  applyBg(); settingsModal.classList.remove('open');
});

exportBtn.addEventListener('click', () => {
  const all = [];
  gridEl.querySelectorAll('.card').forEach(card => {
    const url = card.getAttribute('data-url') || card.href;
    const title = card.getAttribute('data-title') || card.querySelector('.title')?.textContent || '';
    if (url) all.push({ title, url });
  });
  const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'markit-bookmarks.json'; a.click(); URL.revokeObjectURL(a.href);
});
importBtn.addEventListener('click', () => importFile.click());
importFile.addEventListener('change', e => {
  const file = e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      if (!Array.isArray(data)) throw new Error('格式错误');
      const customs = loadCustom();
      const existing = new Set(customs.map(b => b.url));
      let added = 0;
      data.forEach(bm => {
        if (bm.url && !existing.has(bm.url)) {
          customs.push({ title: bm.title || bm.url, url: bm.url, category: bm.category || '本地导入', folder: bm.folder || '本地导入' });
          existing.add(bm.url); added++;
        }
      });
      saveCustom(customs);
      renderCustomCards(); addStaticCardActions(); buildTags(); sortCards(); filter(); updateVisitCounts();
      alert('导入完成，新增 ' + added + ' 个书签');
    } catch (err) { alert('导入失败: ' + err.message); }
  };
  reader.readAsText(file); importFile.value = '';
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { settingsModal.classList.remove('open'); closeBmModal(); }
});

// ---- theme toggle ----
const themeBtn = document.getElementById('themeBtn');
const themeIcon = document.getElementById('themeIcon');
const THEME_KEY = 'markit-theme';
function applyTheme() {
  const theme = localStorage.getItem(THEME_KEY) || 'dark';
  document.body.classList.toggle('light', theme === 'light');
  themeIcon.innerHTML = theme === 'light'
    ? '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
    : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
}
themeBtn.addEventListener('click', () => {
  const cur = localStorage.getItem(THEME_KEY) || 'dark';
  localStorage.setItem(THEME_KEY, cur === 'dark' ? 'light' : 'dark');
  applyTheme();
});

// ---- drag to reorder (custom bookmarks only) ----
let dragCard = null;
gridEl.addEventListener('dragstart', e => {
  const card = e.target.closest('.card.custom');
  if (!card) return;
  dragCard = card;
  card.style.opacity = '0.5';
  e.dataTransfer.effectAllowed = 'move';
});
gridEl.addEventListener('dragover', e => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
});
gridEl.addEventListener('drop', e => {
  e.preventDefault();
  if (!dragCard) return;
  const target = e.target.closest('.card.custom');
  if (target && target !== dragCard) {
    const allCustom = [...gridEl.querySelectorAll('.card.custom')];
    const fromIdx = allCustom.indexOf(dragCard);
    const toIdx = allCustom.indexOf(target);
    if (fromIdx >= 0 && toIdx >= 0) {
      const customs = loadCustom();
      const [moved] = customs.splice(fromIdx, 1);
      customs.splice(toIdx, 0, moved);
      saveCustom(customs);
      renderCustomCards(); addStaticCardActions(); updateVisitCounts(); filter();
    }
  }
  dragCard.style.opacity = '1';
  dragCard = null;
});
gridEl.addEventListener('dragend', () => {
  if (dragCard) { dragCard.style.opacity = '1'; dragCard = null; }
});

// ---- init ----
renderCustomCards();
addStaticCardActions();
applyView();
applyTheme();
applyBg();
switchMode(currentMode);
updateVisitCounts();
checkDuplicates();
</script>
</body>
</html>"""
    js = js.replace('__CATEGORIES__', categories_json)
    js = js.replace('__MODE_LABELS__', mode_labels_json)
    js = js.replace('__RULES__', rules_json)
    js = js.replace('__TOTAL__', str(total))
    parts.append(js)

    html = "".join(parts)
    Path(output).write_text(html, encoding="utf-8")
    return output
