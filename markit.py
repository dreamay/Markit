#!/usr/bin/env python3
"""
MarkIt - 书签收藏管理工具
支持从浏览器导出的书签HTML导入，自动归类，生成静态HTML页面。
"""

import argparse
import sys,os
from pathlib import Path

from markit.config import load_config, _build_rules
from markit.parsers import load_bookmarks, auto_detect_bookmarks
from markit.grouping import group_bookmarks, group_by_folder, group_by_browser
from markit.renderer import generate_html
folder_name = "markit_app"

def main():
    parser = argparse.ArgumentParser(
        description="MarkIt - 书签自动归类，生成静态 HTML（包含所有分类视图）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python markit.py --browser                # 自动从浏览器读取书签
  python markit.py                          # 使用默认 bookmarks.json
  python markit.py -i bookmarks.html        # 从浏览器导出的 HTML 导入
  python markit.py -i my.json -o my.html    # 指定输入输出
        """,
    )
    parser.add_argument("-b", "--browser", action="store_true",
                        help="自动从已安装的浏览器读取书签（Chrome/Edge/Firefox/Safari）")
    parser.add_argument("-i", "--input", default="bookmarks.json",
                        help="书签文件路径，支持 .json 或浏览器导出的 .html (默认: bookmarks.json)")
    parser.add_argument("-o", "--output", default= folder_name + "/index.html",
                        help="输出 HTML 文件路径 (默认: index.html)")
    args = parser.parse_args()

    if args.browser:
        print("正在自动检测浏览器书签...")
        bookmarks = auto_detect_bookmarks()
        if not bookmarks:
            print("未检测到任何浏览器书签，请确认浏览器已安装且有书签数据。")
            sys.exit(1)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误: 找不到文件 {input_path}")
            sys.exit(1)
        bookmarks = load_bookmarks(str(input_path))
    print(f"已加载 {len(bookmarks)} 个书签")

    config = load_config()
    rules = _build_rules(config)

    all_groups = {
        "folder":  group_by_folder(bookmarks),
        "keyword": group_bookmarks(bookmarks, rules),
        "browser": group_by_browser(bookmarks),
    }

    for mode_label, (mode, groups) in zip(
        ["文件夹", "关键词", "浏览器"], all_groups.items()
    ):
        print(f"  [{mode_label}] {len(groups)} 个分类")

    os.makedirs(folder_name, exist_ok=True)
    out = generate_html(all_groups, args.output)
    print(f"\n已生成: {out}")
    print("用浏览器打开即可使用，右上角可切换分类视图，按 / 键可快速搜索")


if __name__ == "__main__":
    main()
