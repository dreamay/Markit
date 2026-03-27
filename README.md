# MarkIt

一款本地功能丰富的书签管理器。

自动归类书签，生成静态 HTML 页面，方便快速查找和打开网址。纯 Python 标准库实现，零依赖。

## 功能特性

- **主页视图** — 常用书签、最近访问、访问最多，一目了然
- **稍后阅读** — 点击书签图标添加到稍后阅读列表
- **三种分类视图** — 文件夹 / 关键词 / 浏览器，左上角实时切换
- **收藏到主页** — 点击 ★ 将书签固定到主页常用栏
- **实时时钟** — 右上角显示当前时间和日期
- **浏览器书签同步** — 在设置中加载浏览器书签文件（HTML/JSON），自动与本地数据合并去重
- **自动同步** — 设置中开启每小时自动同步开关（需 Chrome 扩展环境）
- **一键去重** — 检测到重复网址时，提供一键删除重复书签按钮，只保留一份
- **手动添加书签** — 页面内直接添加，支持选择或新建分类
- **编辑 / 删除 / 复制** — 所有书签 hover 显示操作按钮
- **卡片 / 列表双视图** — 一键切换布局
- **多维排序** — 按名称、时间、最近使用、访问次数
- **访问统计** — 自动记录点击次数
- **重复检测** — 自动高亮重复网址
- **拖拽排序** — 自定义书签支持拖拽调整顺序
- **明暗主题** — dark / light 模式切换
- **自定义背景** — 设置中填入图片链接
- **导入导出** — JSON 格式，导出全部书签
- **实时搜索** — 按 `/` 键快速聚焦搜索框
- **分类管理** — 删除分类下的自定义书签
- **响应式布局** — 适配桌面和移动端
- **零依赖** — 纯 Python 标准库 + 纯前端 localStorage

## 使用方法

```bash
# 自动从浏览器读取书签（Chrome/Edge/Firefox/Safari）
python markit.py --browser

# 从默认 bookmarks.json 生成
python markit.py

# 从浏览器导出的 HTML 导入
python markit.py -i exported_bookmarks.html

# 指定输入输出
python markit.py -i my.json -o my_bookmarks.html
```

生成的 `markit_app/index.html` 用浏览器打开即可使用。

## 页面操作说明

| 操作 | 说明 |
|------|------|
| 左上角分类切换 | 在主页、稍后阅读、文件夹、关键词、浏览器视图间切换 |
| 右上角时钟 | 显示实时时间和日期 |
| `+` 按钮 | 手动添加书签，可选择分类 |
| 🌙 按钮 | 切换明暗主题 |
| ⚙ 设置按钮 | 背景图片、导入导出、浏览器书签同步、自动同步开关 |
| 搜索框（按 `/` 聚焦） | 实时搜索书签标题和域名 |
| 排序下拉 | 按名称 / 时间 / 最近使用 / 访问次数排序 |
| 卡片/列表切换 | 右侧视图切换按钮 |
| 书签 hover | 显示收藏★、稍后阅读、编辑、复制、删除按钮 |
| 分类标签 | 点击筛选，hover 显示删除按钮（仅删除自定义书签） |
| 重复检测横幅 | 自动检测重复网址，可一键去重或忽略 |
| 拖拽 | 自定义书签支持拖拽调整顺序 |

### 浏览器书签同步

1. 打开设置（⚙ 按钮）
2. 在「浏览器书签同步」区域点击「加载浏览器书签」
3. 选择浏览器导出的书签文件（`.html` 或 `.json` 格式）
4. 导入的书签自动与本地数据合并，按 URL 去重
5. 可开启「每小时自动同步」开关（仅在 Chrome 扩展环境下生效）

> 导出浏览器书签：Chrome 中打开 `chrome://bookmarks`，点击右上角 `⋮` → 导出书签。

## 配置文件

在 `config.json` 中自定义关键词分类规则：

```json
{
  "category_rules": {
    "博客": ["blog", "medium.com", "substack"],
    "购物": ["taobao", "jd.com", "amazon"]
  }
}
```

自定义规则会与内置规则合并，用户规则优先。

## 项目结构

```
markit.py              CLI 入口
config.json            用户配置（自定义分类规则）
bookmarks.json         示例书签数据
markit_app/            生成的静态页面目录
  index.html           生成的书签管理页面
markit/                Python 包
  __init__.py
  config.py            分类规则 + 配置加载
  parsers.py           浏览器书签解析（Chrome/Edge/Firefox/Safari/HTML）
  grouping.py          三种分组逻辑（keyword/folder/browser）
  renderer.py          HTML 生成（含前端 CSS/JS）
```

## 项目分支

```
dev                    本地文件方式
dev-crx                插件方式-代码可同时生成本地文件和插件
dev-crx-mvp            插件方式-代码不可生成插件，不过插件可直接使用
```

## 数据存储

- **静态书签**：由 Python 生成时写入 HTML，来源于浏览器或 JSON 文件
- **自定义书签**：存储在浏览器 `localStorage`（键 `markit-custom-bookmarks`）
- **用户偏好**：主题、背景、排序、视图模式等均存储在 `localStorage`
- **访问记录**：点击次数和最近访问记录存储在 `localStorage`

所有数据保存在本地，不上传任何服务器。

## 书签数据格式

`bookmarks.json` 格式：

```json
[
  {"title": "GitHub", "url": "https://github.com"},
  {"title": "Google", "url": "https://www.google.com"}
]
```

也支持浏览器导出的书签 HTML 文件。

## 作者

[dreamsong](http://songit.cn/)
