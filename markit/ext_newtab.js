(async () => {
const RULES = __RULES__;
const MODE_LABELS = {"home":"主页","readlater":"稍后阅读","folder":"文件夹","keyword":"关键词","browser":"浏览器"};
const MODES = ['home','readlater','folder','keyword','browser'];

/* ---- Storage helpers ---- */
function storageGet(keys) {
  return new Promise(r => chrome.storage.local.get(keys, r));
}
function storageSet(obj) {
  return new Promise(r => chrome.storage.local.set(obj, r));
}

/* ---- State ---- */
let allBookmarks = [];
let customBookmarks = [];
let visits = {};
let recent = [];
let pins = [];
let readlater = [];
let currentMode = 'home';
let currentSort = 'name';
let currentView = 'card';
let currentTheme = 'dark';
let currentBg = '';
let autoSync = false;
let lastSync = '';
let activeTag = '';
let editingUrl = null;
let dragSrcEl = null;

/* ---- DOM refs ---- */
const $ = id => document.getElementById(id);
const grid = $('grid');
const homepage = $('homepage');
const toolbar = $('toolbar');
const search = $('search');
const sortSelect = $('sortSelect');
const tags = $('tags');
const stats = $('stats');
const syncBtn = $('syncBtn');
const addBtn = $('addBtn');
const themeBtn = $('themeBtn');
const settingsBtn = $('settingsBtn');
const settingsModal = $('settingsModal');
const settingsCancel = $('settingsCancel');
const settingsSave = $('settingsSave');
const bgInput = $('bgInput');
const exportBtn = $('exportBtn');
const importBtn = $('importBtn');
const importFile = $('importFile');
const syncStatus = $('syncStatus');
const autoSyncToggle = $('autoSyncToggle');
const bmModal = $('bmModal');
const bmModalTitle = $('bmModalTitle');
const bmTitleInput = $('bmTitleInput');
const bmUrlInput = $('bmUrlInput');
const bmCatSelect = $('bmCatSelect');
const bmCancel = $('bmCancel');
const bmSave = $('bmSave');
const dupBanner = $('dupBanner');
const dupText = $('dupText');
const dupDedup = $('dupDedup');
const dupDismiss = $('dupDismiss');
const modeSwitcher = $('modeSwitcher');
const viewToggle = $('viewToggle');
const clockTime = $('clockTime');
const clockDate = $('clockDate');

/* ---- Classify bookmark by URL ---- */
function classifyKeyword(url) {
  const lower = url.toLowerCase();
  for (const [cat, keywords] of Object.entries(RULES)) {
    for (const kw of keywords) {
      if (lower.includes(kw)) return cat;
    }
  }
  return '其他';
}

function getDomain(url) {
  try { return new URL(url).hostname.replace('www.',''); } catch { return url; }
}

function getFavicon(url) {
  try {
    const u = new URL(url);
    return 'https://www.google.com/s2/favicons?domain=' + u.hostname + '&sz=64';
  } catch { return ''; }
}

function makeFallbackIcon(letter) {
  return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#6366f1"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="16">' + letter + '</text></svg>');
}

/* ---- Sync browser bookmarks ---- */
async function syncBrowserBookmarks() {
  syncBtn.classList.add('syncing');
  try {
    const tree = await chrome.bookmarks.getTree();
    const bookmarks = [];
    function walk(nodes, folder) {
      for (const node of nodes) {
        if (node.url && /^https?:/.test(node.url)) {
          bookmarks.push({
            title: node.title || node.url,
            url: node.url,
            folder: folder,
            dateAdded: node.dateAdded || Date.now()
          });
        }
        if (node.children) walk(node.children, node.title || folder);
      }
    }
    walk(tree, '');
    const now = new Date().toISOString();
    await storageSet({ bookmarks: bookmarks, lastsync: now });
    allBookmarks = bookmarks;
    lastSync = now;
    updateSyncStatus();
    render();
  } catch (e) {
    console.error('Sync failed:', e);
  } finally {
    syncBtn.classList.remove('syncing');
  }
}

function updateSyncStatus() {
  if (lastSync) {
    const d = new Date(lastSync);
    syncStatus.textContent = '上次同步: ' + d.toLocaleString('zh-CN');
  } else {
    syncStatus.textContent = '尚未同步';
  }
}

/* ---- Merge all bookmarks ---- */
function getAllItems() {
  const map = new Map();
  for (const bm of allBookmarks) {
    map.set(bm.url, { ...bm });
  }
  for (const bm of customBookmarks) {
    if (!map.has(bm.url)) {
      map.set(bm.url, { ...bm });
    }
  }
  return Array.from(map.values());
}

/* ---- Dedup detection ---- */
function findDuplicates(items) {
  const seen = {};
  const dups = [];
  for (const bm of items) {
    const key = bm.url.replace(/\/$/,'').toLowerCase();
    if (seen[key]) { dups.push(bm.url); } else { seen[key] = true; }
  }
  return dups;
}

function dedup() {
  const items = getAllItems();
  const seen = new Set();
  const unique = [];
  for (const bm of items) {
    const key = bm.url.replace(/\/$/,'').toLowerCase();
    if (!seen.has(key)) { seen.add(key); unique.push(bm); }
  }
  allBookmarks = unique.filter(function(b) { return !customBookmarks.find(function(c) { return c.url === b.url; }); });
  customBookmarks = unique.filter(function(b) { return customBookmarks.find(function(c) { return c.url === b.url; }); });
  storageSet({ bookmarks: allBookmarks, customBookmarks: customBookmarks });
  dupBanner.classList.remove('show');
  render();
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

/* ---- Build card ---- */
function buildCard(bm) {
  const domain = getDomain(bm.url);
  const favicon = getFavicon(bm.url);
  const kwCat = classifyKeyword(bm.url);
  const folder = bm.folder || '';
  const isPinned = pins.includes(bm.url);
  const isReadLater = readlater.includes(bm.url);
  const visitCount = visits[bm.url] || 0;
  const searchStr = (bm.title + ' ' + domain + ' ' + folder + ' ' + kwCat).toLowerCase();

  const card = document.createElement('a');
  card.className = 'card';
  card.href = bm.url;
  card.target = '_self';
  card.draggable = true;
  card.dataset.url = bm.url;
  card.dataset.title = bm.title;
  card.dataset.search = searchStr;
  card.dataset.catFolder = folder;
  card.dataset.catKeyword = kwCat;
  card.dataset.catBrowser = folder;
  card.dataset.dateAdded = bm.dateAdded || 0;

  var img = document.createElement('img');
  img.className = 'favicon';
  img.src = favicon;
  img.alt = '';
  img.addEventListener('error', function() {
    this.src = makeFallbackIcon(bm.title.charAt(0).toUpperCase());
  });
  card.appendChild(img);

  var info = document.createElement('div');
  info.className = 'info';
  info.innerHTML = '<div class="title">' + escHtml(bm.title) + '</div>'
    + '<div class="domain">' + escHtml(domain) + '</div>'
    + (visitCount > 0 ? '<div class="visit-count">访问 ' + visitCount + ' 次</div>' : '');
  card.appendChild(info);

  var actions = document.createElement('div');
  actions.className = 'card-actions';
  actions.innerHTML = '<button class="card-action pin-action' + (isPinned ? ' pinned' : '') + '" title="置顶"><svg width="12" height="12" viewBox="0 0 24 24" fill="' + (isPinned ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></button>'
    + '<button class="card-action readlater-action' + (isReadLater ? ' marked' : '') + '" title="稍后阅读"><svg width="12" height="12" viewBox="0 0 24 24" fill="' + (isReadLater ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>'
    + '<button class="card-action edit-action" title="编辑"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>'
    + '<button class="card-action copy-action" title="复制链接"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>'
    + '<button class="card-action delete-action" title="删除"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>';
  card.appendChild(actions);

  /* Card click - track visit */
  card.addEventListener('click', function(e) {
    if (e.target.closest('.card-action')) { e.preventDefault(); return; }
    visits[bm.url] = (visits[bm.url] || 0) + 1;
    recent = [bm.url].concat(recent.filter(function(u) { return u !== bm.url; })).slice(0, 50);
    storageSet({ visits: visits, recent: recent });
  });

  card.querySelector('.pin-action').addEventListener('click', function(e) {
    e.preventDefault(); e.stopPropagation();
    if (pins.includes(bm.url)) { pins = pins.filter(function(u) { return u !== bm.url; }); }
    else { pins.push(bm.url); }
    storageSet({ pins: pins });
    render();
  });

  card.querySelector('.readlater-action').addEventListener('click', function(e) {
    e.preventDefault(); e.stopPropagation();
    if (readlater.includes(bm.url)) { readlater = readlater.filter(function(u) { return u !== bm.url; }); }
    else { readlater.push(bm.url); }
    storageSet({ readlater: readlater });
    render();
  });

  card.querySelector('.edit-action').addEventListener('click', function(e) {
    e.preventDefault(); e.stopPropagation();
    openEditModal(bm);
  });

  card.querySelector('.copy-action').addEventListener('click', function(e) {
    e.preventDefault(); e.stopPropagation();
    navigator.clipboard.writeText(bm.url);
  });

  card.querySelector('.delete-action').addEventListener('click', function(e) {
    e.preventDefault(); e.stopPropagation();
    if (!confirm('删除书签 "' + bm.title + '"？')) return;
    allBookmarks = allBookmarks.filter(function(b) { return b.url !== bm.url; });
    customBookmarks = customBookmarks.filter(function(b) { return b.url !== bm.url; });
    storageSet({ bookmarks: allBookmarks, customBookmarks: customBookmarks });
    render();
  });

  /* Drag */
  card.addEventListener('dragstart', function(e) { dragSrcEl = card; card.style.opacity = '0.4'; e.dataTransfer.effectAllowed = 'move'; });
  card.addEventListener('dragend', function() { card.style.opacity = '1'; });
  card.addEventListener('dragover', function(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
  card.addEventListener('drop', function(e) {
    e.preventDefault();
    if (dragSrcEl !== card) {
      var parent = card.parentNode;
      var cards = Array.from(parent.querySelectorAll('.card'));
      var fromIdx = cards.indexOf(dragSrcEl);
      var toIdx = cards.indexOf(card);
      if (fromIdx < toIdx) { parent.insertBefore(dragSrcEl, card.nextSibling); }
      else { parent.insertBefore(dragSrcEl, card); }
    }
  });

  return card;
}

/* ---- Render ---- */
function render() {
  var items = getAllItems();
  var q = search.value.toLowerCase().trim();

  stats.textContent = '共 ' + items.length + ' 个书签 · ' + pins.length + ' 个置顶 · ' + readlater.length + ' 个稍后阅读';

  var dups = findDuplicates(items);
  if (dups.length > 0) {
    dupText.textContent = '发现 ' + dups.length + ' 个重复书签';
    dupBanner.classList.add('show');
  } else {
    dupBanner.classList.remove('show');
  }

  if (currentMode === 'home') {
    grid.style.display = 'none';
    toolbar.style.display = 'none';
    homepage.classList.add('active');
    renderHomepage(items);
    return;
  }

  if (currentMode === 'readlater') {
    grid.style.display = '';
    toolbar.style.display = '';
    homepage.classList.remove('active');
    var rlItems = items.filter(function(b) { return readlater.includes(b.url); });
    renderGrid(rlItems, q);
    renderTags(rlItems, 'keyword');
    return;
  }

  grid.style.display = '';
  toolbar.style.display = '';
  homepage.classList.remove('active');
  renderTags(items, currentMode);
  renderGrid(items, q);
}

function renderHomepage(items) {
  var pinnedItems = items.filter(function(b) { return pins.includes(b.url); });
  var recentItems = recent.map(function(u) { return items.find(function(b) { return b.url === u; }); }).filter(Boolean).slice(0, 12);
  var mostVisited = items.slice().sort(function(a, b) { return (visits[b.url]||0) - (visits[a.url]||0); }).filter(function(b) { return (visits[b.url]||0) > 0; }).slice(0, 12);

  homepage.innerHTML = '';

  function makeSection(iconSvg, title, list, emptyMsg) {
    var sec = document.createElement('div');
    sec.className = 'home-section';
    sec.innerHTML = '<div class="home-section-title">' + iconSvg + title + '</div>';
    if (list.length === 0) {
      sec.innerHTML += '<div class="home-empty">' + emptyMsg + '</div>';
    } else {
      var g = document.createElement('div');
      g.className = 'home-grid';
      list.forEach(function(b) { g.appendChild(buildCard(b)); });
      sec.appendChild(g);
    }
    homepage.appendChild(sec);
  }

  makeSection('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>', '置顶书签', pinnedItems, '暂无置顶书签，点击卡片上的星标图标添加');
  makeSection('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>', '最近访问', recentItems, '暂无最近访问记录');
  makeSection('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>', '常用书签', mostVisited, '暂无访问数据');
}

function renderTags(items, groupBy) {
  var cats = new Map();
  for (var i = 0; i < items.length; i++) {
    var bm = items[i];
    var cat;
    if (groupBy === 'folder' || groupBy === 'browser') {
      cat = bm.folder || '未分类';
    } else {
      cat = classifyKeyword(bm.url);
    }
    cats.set(cat, (cats.get(cat) || 0) + 1);
  }

  tags.innerHTML = '';
  var allTag = document.createElement('button');
  allTag.className = 'tag' + (activeTag === '' ? ' active' : '');
  allTag.textContent = '全部 (' + items.length + ')';
  allTag.addEventListener('click', function() { activeTag = ''; render(); });
  tags.appendChild(allTag);

  var sorted = Array.from(cats.entries()).sort(function(a, b) { return b[1] - a[1]; });
  for (var j = 0; j < sorted.length; j++) {
    (function(cat, count) {
      var t = document.createElement('button');
      t.className = 'tag' + (activeTag === cat ? ' active' : '');
      t.textContent = cat + ' (' + count + ')';
      t.addEventListener('click', function() { activeTag = (activeTag === cat ? '' : cat); render(); });
      tags.appendChild(t);
    })(sorted[j][0], sorted[j][1]);
  }
}

function renderGrid(items, q) {
  grid.innerHTML = '';
  var filtered = items;
  if (activeTag) {
    filtered = items.filter(function(bm) {
      if (currentMode === 'folder' || currentMode === 'browser') {
        return (bm.folder || '未分类') === activeTag;
      }
      return classifyKeyword(bm.url) === activeTag;
    });
  }
  if (q) {
    filtered = filtered.filter(function(bm) {
      var s = (bm.title + ' ' + getDomain(bm.url) + ' ' + (bm.folder || '') + ' ' + classifyKeyword(bm.url)).toLowerCase();
      return s.includes(q);
    });
  }
  filtered = sortItems(filtered);
  filtered.sort(function(a, b) {
    var ap = pins.includes(a.url) ? 0 : 1;
    var bp = pins.includes(b.url) ? 0 : 1;
    return ap - bp;
  });
  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty">没有找到匹配的书签</div>';
    return;
  }
  for (var i = 0; i < filtered.length; i++) {
    grid.appendChild(buildCard(filtered[i]));
  }
}

function sortItems(items) {
  var arr = items.slice();
  switch (currentSort) {
    case 'name':
      arr.sort(function(a, b) { return a.title.localeCompare(b.title, 'zh-CN'); });
      break;
    case 'time':
      arr.sort(function(a, b) { return (b.dateAdded || 0) - (a.dateAdded || 0); });
      break;
    case 'recent':
      arr.sort(function(a, b) {
        var ai = recent.indexOf(a.url);
        var bi = recent.indexOf(b.url);
        return (ai === -1 ? 9999 : ai) - (bi === -1 ? 9999 : bi);
      });
      break;
    case 'visits':
      arr.sort(function(a, b) { return (visits[b.url] || 0) - (visits[a.url] || 0); });
      break;
  }
  return arr;
}

/* ---- Mode switcher ---- */
function renderModeSwitcher() {
  modeSwitcher.innerHTML = '';
  for (var i = 0; i < MODES.length; i++) {
    (function(mode) {
      var btn = document.createElement('button');
      btn.className = 'mode-btn' + (currentMode === mode ? ' active' : '');
      btn.textContent = MODE_LABELS[mode];
      btn.addEventListener('click', function() {
        currentMode = mode;
        activeTag = '';
        storageSet({ mode: currentMode });
        renderModeSwitcher();
        render();
      });
      modeSwitcher.appendChild(btn);
    })(MODES[i]);
  }
}

/* ---- View toggle ---- */
viewToggle.addEventListener('click', function(e) {
  var btn = e.target.closest('.view-btn');
  if (!btn) return;
  currentView = btn.dataset.view;
  viewToggle.querySelectorAll('.view-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  grid.classList.toggle('list-view', currentView === 'list');
  storageSet({ view: currentView });
});

/* ---- Sort ---- */
sortSelect.addEventListener('change', function() {
  currentSort = sortSelect.value;
  storageSet({ sort: currentSort });
  render();
});

/* ---- Search ---- */
search.addEventListener('input', function() { render(); });
document.addEventListener('keydown', function(e) {
  if (e.key === '/' && document.activeElement !== search) {
    e.preventDefault();
    search.focus();
  }
  if (e.key === 'Escape') {
    search.blur();
    search.value = '';
    settingsModal.classList.remove('open');
    bmModal.classList.remove('open');
    render();
  }
});

/* ---- Theme ---- */
function applyTheme(theme) {
  currentTheme = theme;
  document.body.classList.toggle('light', theme === 'light');
  var icon = document.getElementById('themeIcon');
  if (theme === 'light') {
    icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
  } else {
    icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
  }
}

function applyBg(url) {
  if (url) {
    document.body.style.backgroundImage = 'url(' + url + ')';
  } else {
    document.body.style.backgroundImage = '';
  }
}

themeBtn.addEventListener('click', function() {
  var next = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  storageSet({ theme: next });
});

/* ---- Clock ---- */
function updateClock() {
  var now = new Date();
  clockTime.textContent = now.toLocaleTimeString('zh-CN', { hour12: false });
  clockDate.textContent = now.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', weekday: 'short' });
}
updateClock();
setInterval(updateClock, 1000);

/* ---- Settings modal ---- */
settingsBtn.addEventListener('click', function() {
  bgInput.value = currentBg;
  autoSyncToggle.checked = autoSync;
  updateSyncStatus();
  settingsModal.classList.add('open');
});
settingsCancel.addEventListener('click', function() { settingsModal.classList.remove('open'); });
settingsModal.addEventListener('click', function(e) { if (e.target === settingsModal) settingsModal.classList.remove('open'); });

settingsSave.addEventListener('click', async function() {
  currentBg = bgInput.value.trim();
  autoSync = autoSyncToggle.checked;
  applyBg(currentBg);
  await storageSet({ bg: currentBg, autosync: autoSync });
  settingsModal.classList.remove('open');
});

/* ---- Export / Import ---- */
exportBtn.addEventListener('click', function() {
  var data = { bookmarks: allBookmarks, customBookmarks: customBookmarks, visits: visits, recent: recent, pins: pins, readlater: readlater };
  var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'markit-backup-' + new Date().toISOString().slice(0,10) + '.json';
  a.click();
  URL.revokeObjectURL(a.href);
});

importBtn.addEventListener('click', function() { importFile.click(); });
importFile.addEventListener('change', async function(e) {
  var file = e.target.files[0];
  if (!file) return;
  try {
    var text = await file.text();
    var data = JSON.parse(text);
    if (data.bookmarks) { allBookmarks = data.bookmarks; }
    if (data.customBookmarks) { customBookmarks = data.customBookmarks; }
    if (data.visits) { visits = data.visits; }
    if (data.recent) { recent = data.recent; }
    if (data.pins) { pins = data.pins; }
    if (data.readlater) { readlater = data.readlater; }
    await storageSet({ bookmarks: allBookmarks, customBookmarks: customBookmarks, visits: visits, recent: recent, pins: pins, readlater: readlater });
    render();
    alert('导入成功！');
  } catch (err) {
    alert('导入失败: ' + err.message);
  }
  importFile.value = '';
});

/* ---- Add / Edit bookmark modal ---- */
function populateCatSelect() {
  bmCatSelect.innerHTML = '';
  var cats = [''].concat(Object.keys(RULES)).concat(['其他']);
  for (var i = 0; i < cats.length; i++) {
    var opt = document.createElement('option');
    opt.value = cats[i];
    opt.textContent = cats[i] || '自动分类';
    bmCatSelect.appendChild(opt);
  }
}

addBtn.addEventListener('click', function() {
  editingUrl = null;
  bmModalTitle.textContent = '添加书签';
  bmTitleInput.value = '';
  bmUrlInput.value = '';
  populateCatSelect();
  bmModal.classList.add('open');
});

function openEditModal(bm) {
  editingUrl = bm.url;
  bmModalTitle.textContent = '编辑书签';
  bmTitleInput.value = bm.title;
  bmUrlInput.value = bm.url;
  populateCatSelect();
  bmCatSelect.value = bm.folder || '';
  bmModal.classList.add('open');
}

bmCancel.addEventListener('click', function() { bmModal.classList.remove('open'); });
bmModal.addEventListener('click', function(e) { if (e.target === bmModal) bmModal.classList.remove('open'); });

bmSave.addEventListener('click', async function() {
  var title = bmTitleInput.value.trim();
  var url = bmUrlInput.value.trim();
  if (!title || !url) { alert('请填写标题和 URL'); return; }
  var folder = bmCatSelect.value;

  if (editingUrl) {
    var idx1 = allBookmarks.findIndex(function(b) { return b.url === editingUrl; });
    if (idx1 !== -1) {
      allBookmarks[idx1] = Object.assign({}, allBookmarks[idx1], { title: title, url: url, folder: folder || allBookmarks[idx1].folder });
    }
    var idx2 = customBookmarks.findIndex(function(b) { return b.url === editingUrl; });
    if (idx2 !== -1) {
      customBookmarks[idx2] = Object.assign({}, customBookmarks[idx2], { title: title, url: url, folder: folder || customBookmarks[idx2].folder });
    }
    if (editingUrl !== url) {
      pins = pins.map(function(u) { return u === editingUrl ? url : u; });
      readlater = readlater.map(function(u) { return u === editingUrl ? url : u; });
      recent = recent.map(function(u) { return u === editingUrl ? url : u; });
      if (visits[editingUrl]) { visits[url] = visits[editingUrl]; delete visits[editingUrl]; }
    }
  } else {
    customBookmarks.push({ title: title, url: url, folder: folder || classifyKeyword(url), dateAdded: Date.now() });
  }

  await storageSet({ bookmarks: allBookmarks, customBookmarks: customBookmarks, visits: visits, recent: recent, pins: pins, readlater: readlater });
  bmModal.classList.remove('open');
  render();
});

/* ---- Dup banner ---- */
dupDedup.addEventListener('click', dedup);
dupDismiss.addEventListener('click', function() { dupBanner.classList.remove('show'); });

/* ---- Sync button ---- */
syncBtn.addEventListener('click', syncBrowserBookmarks);

/* ---- Auto sync ---- */
function checkAutoSync() {
  if (!autoSync) return;
  if (!lastSync) { syncBrowserBookmarks(); return; }
  var elapsed = Date.now() - new Date(lastSync).getTime();
  if (elapsed > 3600000) { syncBrowserBookmarks(); }
}

/* ---- Init ---- */
try {
  var stored = await storageGet([
    'bookmarks','customBookmarks','visits','recent','pins','readlater',
    'theme','bg','mode','sort','view','autosync','lastsync'
  ]);

  allBookmarks = stored.bookmarks || [];
  customBookmarks = stored.customBookmarks || [];
  visits = stored.visits || {};
  recent = stored.recent || [];
  pins = stored.pins || [];
  readlater = stored.readlater || [];
  currentTheme = stored.theme || 'dark';
  currentBg = stored.bg || '';
  currentMode = stored.mode || 'home';
  currentSort = stored.sort || 'name';
  currentView = stored.view || 'card';
  autoSync = stored.autosync || false;
  lastSync = stored.lastsync || '';

  applyTheme(currentTheme);
  applyBg(currentBg);
  sortSelect.value = currentSort;
  if (currentView === 'list') {
    grid.classList.add('list-view');
    viewToggle.querySelectorAll('.view-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.view === 'list');
    });
  }

  renderModeSwitcher();

  if (allBookmarks.length === 0) {
    await syncBrowserBookmarks();
  } else {
    render();
    checkAutoSync();
  }
} catch (err) {
  console.error('Init error:', err);
  renderModeSwitcher();
  render();
}

})();
