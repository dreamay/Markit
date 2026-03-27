# MarkIt

一款本地功能丰富的书签管理器。

自动归类书签，生成静态 HTML 页面，方便快速查找和打开网址。纯 Python 标准库实现，零依赖。

## 功能特性

- **三种分类视图** — 文件夹 / 关键词 / 浏览器，右上角实时切换
- **手动添加书签** — 页面内直接添加，支持选择或新建分类
- **编辑 / 删除 / 分享** — 所有书签 hover 显示操作按钮
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
# 自动从浏览器读取书签
python markit.py --browser

# 从默认 bookmarks.json 生成
python markit.py

# 从浏览器导出的 HTML 导入
python markit.py -i exported_bookmarks.html

# 指定输入输出
python markit.py -i my.json -o my_bookmarks.html
```

生成 `index.html` 后用浏览器打开即可。

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
markit/                Python 包
  __init__.py
  config.py            分类规则 + 配置加载
  parsers.py           浏览器书签解析（Chrome/Edge/Firefox/Safari/HTML）
  grouping.py          三种分组逻辑（keyword/folder/browser）
  renderer.py          HTML 生成
```

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
