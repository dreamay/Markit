MarkIt - 书签收藏管理工具
==========================

自动归类书签，生成静态 HTML 页面，方便快速查找和打开网址。
纯 Python 标准库实现，零依赖。

生成的页面包含三种分类视图（文件夹 / 关键词 / 浏览器），可在页面右上角实时切换，无需重新运行脚本。


使用方法
--------

1. 自动从浏览器读取书签：

   python markit.py --browser

2. 默认用法（读取 bookmarks.json，生成 index.html）：

   python markit.py

3. 从浏览器导出的书签 HTML 导入：

   python markit.py -i exported_bookmarks.html

4. 指定输入输出文件：

   python markit.py -i my.json -o my_bookmarks.html

5. 用浏览器打开生成的 HTML 即可使用。


分类视图
--------

生成的页面右上角有模式切换器，支持三种视图实时切换：

- 文件夹：按浏览器中的书签文件夹结构分类，保留原有的文件夹组织
- 关键词（默认）：根据 URL 中的域名关键词自动分类，未匹配的归入"其他"
- 浏览器：按来源浏览器（Chrome/Edge/Firefox/Safari）分类

页面会记住上次选择的视图模式，刷新后自动恢复。


配置文件 config.json
--------------------

在 markit.py 同目录下创建 config.json 可自定义关键词分类规则：

{
  "category_rules": {
    "我的自定义分类": ["keyword1", "keyword2"]
  }
}

- category_rules：自定义关键词规则（可选），会与内置规则合并，用户规则优先

示例：添加自定义分类规则：

{
  "category_rules": {
    "博客": ["blog", "medium.com", "substack"],
    "购物": ["taobao", "jd.com", "amazon"]
  }
}


项目结构
--------

markit.py          CLI 入口（精简，仅 argparse + 调用）
config.json        用户配置
readme.txt         本文档
bookmarks.json     示例数据
index.html         生成产物

markit/            Python 包
  __init__.py      包标记
  config.py        配置加载（CATEGORY_RULES、load_config、_build_rules）
  parsers.py       浏览器书签解析（Chrome/Edge/Firefox/Safari/HTML）
  grouping.py      分类逻辑（keyword/folder/browser 三种分组函数）
  renderer.py      HTML 生成（generate_html）


书签数据格式
------------

bookmarks.json 格式如下，每条书签包含 title 和 url：

[
  {"title": "GitHub", "url": "https://github.com"},
  {"title": "Google", "url": "https://www.google.com"}
]

也可以直接使用浏览器导出的书签 HTML 文件：
- Chrome: 书签管理器 -> 右上角菜单 -> 导出书签
- Firefox: 书签 -> 管理书签 -> 导入和备份 -> 将书签导出为 HTML


自动归类规则（关键词视图）
----------------------------

程序根据 URL 中的域名关键词自动分类，预设分类包括：

- 开发工具（github, gitlab, stackoverflow, npmjs 等）
- 编程文档（docs.python, developer.mozilla 等）
- AI / 人工智能（openai, claude, huggingface 等）
- 搜索引擎（google.com, bing.com 等）
- 社交媒体（twitter, x.com, reddit 等）
- 视频 / 媒体（youtube, bilibili 等）
- 新闻 / 资讯（news.ycombinator, techcrunch 等）
- 知识 / 百科（wikipedia, zhihu, douban 等）
- 云服务（console.aws, cloud.google 等）
- 刷题 / 学习（leetcode, coursera 等）
- 其他（未匹配的书签）

如需自定义分类规则，在 config.json 的 category_rules 中添加即可。


HTML 页面功能
-------------

- 模式切换：右上角切换文件夹/关键词/浏览器视图，实时更新，记忆选择
- 分类标签筛选：点击顶部标签切换分类
- 实时搜索：输入关键词即时过滤，按 / 键快速聚焦搜索框
- 网站图标：自动获取各网站的 favicon
- 响应式布局：适配桌面和移动端
