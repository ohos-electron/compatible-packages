#!/usr/bin/env python3
"""
从一个或多个 Electron 兼容性分析结果 xlsx 生成兼容包数据：
- data/*.md        Markdown 表格（GitHub 在线浏览）
- data/*.jsonl     JSONL 格式（命令行 grep/jq 查询，搜索页数据源）
- data/index.json  索引文件（总数、更新日期、各文件条目数）
- README.md        仓库首页

合并规则：所有文件的所有行按包名分组，取「生成时间」最新的一行（时间相同时命令行里靠后的文件优先）；
最新一行「状态 = 通过」才收录，版本取这一行的。所以同一个包后来验证失败会被移出，新版本验证通过会替换旧版本。
进程字段：取该包同一版本、带「主进程 / 渲染进程」列的最新一行，「是」写成 main / renderer = true；
「否」只表示当次没有在那个进程验证，不写字段（搜索页显示「—」），不当作不兼容。

用法：python3 gen_packages.py <xlsx> [<xlsx> ...] [--repo owner/name] [--electron 34]
"""

import argparse
import glob
import re
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from openpyxl import load_workbook

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
README_FILE = os.path.join(SCRIPT_DIR, "README.md")

SHEET_NAME = "包结论汇总"
COL_STATUS = "状态"
COL_NAME = "包名"
COL_VERSION = "版本"
COL_TIME = "生成时间"
COL_MAIN = "主进程"
COL_RENDERER = "渲染进程"
PASS_STATUS = "通过"
YES = "是"
PROCESS_FIELDS = (("main", COL_MAIN, "主进程"), ("renderer", COL_RENDERER, "渲染进程"))
NO_TIME = datetime.min.replace(tzinfo=timezone.utc)
LETTERS = list("abcdefghijklmnopqrstuvwxyz") + ["0-9"]


def get_sort_key(name):
    if name.startswith("@"):
        parts = name.split("/", 1)
        if len(parts) == 2:
            return (parts[0][1:].lower() + "/" + parts[1].lower(),)
        return (name.lower(),)
    return (name.lower(),)


def get_first_letter(name):
    if name.startswith("@"):
        after_at = name[1:]
        if after_at:
            c = after_at[0].lower()
            return c if "a" <= c <= "z" else "0-9"
    c = name[0].lower() if name else "_"
    return c if "a" <= c <= "z" else "0-9"


def cell_str(value):
    return str(value).strip() if value is not None else ""


def parse_time(value):
    """「生成时间」：2026-10-18 11:26:00 UTC 或 ISO 8601（带时区）。认不出时返回 NO_TIME，只按文件顺序比较。"""
    text = cell_str(value)
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.\d+)?\s*(UTC|Z)?", text)
    if m:
        return datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}").replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return NO_TIME


def read_rows(xlsx_path):
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb[SHEET_NAME] if SHEET_NAME in wb.sheetnames else wb.active
    rows = ws.iter_rows(values_only=True)

    header = [cell_str(h) for h in next(rows)]
    missing = [c for c in (COL_STATUS, COL_NAME, COL_VERSION) if c not in header]
    if missing:
        sys.exit(f"{xlsx_path} 表头缺少列：{', '.join(missing)}（sheet：{ws.title}）")
    index = {h: i for i, h in enumerate(header) if h}

    out = []
    for row in rows:
        get = lambda col: cell_str(row[index[col]]) if col in index and index[col] < len(row) else ""
        name = get(COL_NAME) if row else ""
        if not name:
            continue
        out.append({"name": name, "version": get(COL_VERSION) or "latest", "status": get(COL_STATUS),
                    "time": parse_time(get(COL_TIME)), **{field: get(col) for field, col, _ in PROCESS_FIELDS}})
    wb.close()

    passed = sum(1 for r in out if r["status"] == PASS_STATUS)
    extra = "，含进程列" if any(col in index for _, col, _ in PROCESS_FIELDS) else ""
    print(f"  {os.path.basename(xlsx_path)}（sheet「{ws.title}」）：{len(out)} 行，通过 {passed}{extra}")
    return out


def read_packages(xlsx_paths):
    latest = {}      # 包名 → (排序键, 行)
    processes = {}   # (包名, 版本) → (排序键, 带进程列的行)
    for order, path in enumerate(xlsx_paths):
        for r in read_rows(path):
            key = (r["time"], order)
            if r["name"] not in latest or key >= latest[r["name"]][0]:
                latest[r["name"]] = (key, r)
            if any(r[field] for field, _, _ in PROCESS_FIELDS):
                pk = (r["name"], r["version"])
                if pk not in processes or key >= processes[pk][0]:
                    processes[pk] = (key, r)

    packages = []
    for name, (_, r) in latest.items():
        if r["status"] != PASS_STATUS:
            continue
        p = {"name": name, "version": r["version"]}
        proc = processes.get((name, r["version"]))
        for field, _, _ in PROCESS_FIELDS:
            if proc and proc[1][field] == YES:
                p[field] = True
        packages.append(p)

    with_proc = sum(1 for p in packages if any(f in p for f, _, _ in PROCESS_FIELDS))
    print(f"合并 {len(xlsx_paths)} 个文件：收录 {len(packages)} 个（最新一次结果为「{PASS_STATUS}」），"
          f"其中有进程信息 {with_proc} 个；未收录 {len(latest) - len(packages)} 个（最新一次结果为失败/受阻/有条件通过）")
    return sorted(packages, key=lambda p: get_sort_key(p["name"]))


def process_text(p):
    return "、".join(label for field, _, label in PROCESS_FIELDS if p.get(field)) or "—"


def write_data(packages, electron_versions, repo):
    groups = defaultdict(list)
    for p in packages:
        groups[get_first_letter(p["name"])].append(p)

    os.makedirs(DATA_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(DATA_DIR, "*.jsonl")) + glob.glob(os.path.join(DATA_DIR, "*.md")):
        os.remove(old)

    file_counts = {}
    for letter in LETTERS:
        entries = groups.get(letter)
        if not entries:
            continue
        with open(os.path.join(DATA_DIR, f"{letter}.md"), "w", encoding="utf-8") as f:
            f.write(f"# 字母 {letter.upper()} 开头的兼容包（{len(entries)} 个）\n\n")
            f.write("> [← 返回首页](../README.md)\n\n")
            f.write("| 包名 | 版本 | 进程 |\n")
            f.write("|------|------|------|\n")
            for p in entries:
                f.write(f"| `{p['name']}` | {p['version']} | {process_text(p)} |\n")

        with open(os.path.join(DATA_DIR, f"{letter}.jsonl"), "w", encoding="utf-8") as f:
            for p in entries:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        file_counts[f"{letter}.jsonl"] = len(entries)
        print(f"  {letter}: {len(entries)}")

    index_data = {
        "total": len(packages),
        "last_updated": str(date.today()),
        "electron_versions": electron_versions,
        "repo": repo,
        "files": file_counts,
    }
    with open(os.path.join(DATA_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return index_data


def write_readme(index_data):
    repo = index_data["repo"]
    owner, name = repo.split("/", 1)
    site_url = f"https://{owner.lower()}.github.io/{name}/"
    repo_url = f"https://github.com/{repo}"
    ev = " / ".join(index_data["electron_versions"])
    ev_arg = ",".join(index_data["electron_versions"])

    letter_rows = "\n".join(
        f"| {letter.upper()} | {index_data['files'][f'{letter}.jsonl']:,} | [{letter.upper()}](data/{letter}.md) |"
        for letter in LETTERS
        if f"{letter}.jsonl" in index_data["files"]
    )

    readme = f"""# {name}

已在鸿蒙 PC 的 Electron {ev} 上验证通过的 npm 包列表。这些包可直接在该 Electron 环境中使用，无需额外适配。

## 📊 统计摘要

> 更新日期：{index_data['last_updated']} | 兼容包总数：**{index_data['total']:,}**

## 🔍 在线查询

👉 **[点击打开搜索页]({site_url})**（支持按包名搜索 + 按字母浏览）

**按字母浏览**（GitHub Markdown 表格）：

| 字母 | 包数量 | 浏览表格 |
|------|--------|---------|
{letter_rows}

> 💡 在表格页面中可使用浏览器 `Ctrl+F` 搜索包名。

## ⚠️ 免责声明

兼容性验证结果由 AI 自动验证生成，可能存在部分与实际不符的情况。如发现错误，欢迎 [提交 Issue]({repo_url}/issues) 反馈。

## 📁 项目结构

```
├── index.html               # GitHub Pages 搜索页
├── gen_packages.py          # 数据生成脚本
└── data/
    ├── index.json           # 索引（总条目数、各文件条目数）
    ├── *.md                 # Markdown 表格（GitHub 在线浏览）
    └── *.jsonl              # JSONL 格式（命令行 grep/jq 查询）
```

## 📖 使用方式

### 命令行查询

```bash
git clone {repo_url}.git
cd {name}

# 模糊搜索
grep "lodash" data/l.jsonl

# 精确搜索（scoped 包按 @ 后的首字母分组）
jq -c 'select(.name == "lodash")' data/l.jsonl
jq -c 'select(.name == "@electron/remote")' data/e.jsonl
```

### 程序中引用

```javascript
const fs = require('fs');
const packages = fs.readFileSync('data/l.jsonl', 'utf8')
  .trim().split('\\n').map(JSON.parse);
```

每条记录有 `name`、`version`；已确认可在对应进程使用时，还有 `"main": true`（主进程）/ `"renderer": true`（渲染进程）。没有这两个字段表示进程未标注，不代表不兼容。

## 🔧 数据更新

```bash
# 1. 准备新的分析结果 xlsx（sheet「{SHEET_NAME}」，含「{COL_STATUS}」「{COL_NAME}」「{COL_VERSION}」「{COL_TIME}」列，可选「{COL_MAIN}」「{COL_RENDERER}」列）
# 2. 把历次分析结果 xlsx 全部传入（新结果追加在最后）：每个包取「{COL_TIME}」最新的一行，状态为「{PASS_STATUS}」才收录
python3 gen_packages.py <xlsx> [<xlsx> ...] --repo {repo} --electron {ev_arg}
# 3. 提交
git add -A && git commit -m "update: 更新兼容包列表"
git push
```
"""
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme)


def main():
    parser = argparse.ArgumentParser(description="从 xlsx 生成 Electron 兼容包数据")
    parser.add_argument("xlsx", nargs="+", help="分析结果 xlsx 文件路径，可多个（按生成时间合并）")
    parser.add_argument("--repo", default="ohos-electron/compatible-packages", help="GitHub 仓库 owner/name")
    parser.add_argument("--electron", default="34", help="支持的 Electron 主版本，逗号分隔")
    args = parser.parse_args()

    missing = [p for p in args.xlsx if not os.path.isfile(p)]
    if missing:
        sys.exit(f"文件不存在：{', '.join(missing)}")
    if "/" not in args.repo:
        sys.exit("--repo 格式应为 owner/name")

    print(f"读取 {len(args.xlsx)} 个文件：")
    packages = read_packages(args.xlsx)
    electron_versions = [v.strip() for v in args.electron.split(",") if v.strip()]
    index_data = write_data(packages, electron_versions, args.repo)
    write_readme(index_data)
    print(f"Done: {index_data['total']} packages, {len(index_data['files'])} files")


if __name__ == "__main__":
    main()
