# compatible-packages

已在鸿蒙 PC 的 Electron 34 上验证通过的 npm 包列表。这些包可直接在该 Electron 环境中使用，无需额外适配。

## 📊 统计摘要

> 更新日期：2026-10-29 | 兼容包总数：**749**

## 🔍 在线查询

👉 **[点击打开搜索页](https://ohos-electron.github.io/compatible-packages/)**（支持按包名搜索 + 按字母浏览）

**按字母浏览**（GitHub Markdown 表格）：

| 字母 | 包数量 | 浏览表格 |
|------|--------|---------|
| A | 34 | [A](data/a.md) |
| B | 26 | [B](data/b.md) |
| C | 53 | [C](data/c.md) |
| D | 37 | [D](data/d.md) |
| E | 47 | [E](data/e.md) |
| F | 21 | [F](data/f.md) |
| G | 13 | [G](data/g.md) |
| H | 25 | [H](data/h.md) |
| I | 35 | [I](data/i.md) |
| J | 23 | [J](data/j.md) |
| K | 5 | [K](data/k.md) |
| L | 29 | [L](data/l.md) |
| M | 56 | [M](data/m.md) |
| N | 21 | [N](data/n.md) |
| O | 10 | [O](data/o.md) |
| P | 46 | [P](data/p.md) |
| Q | 11 | [Q](data/q.md) |
| R | 55 | [R](data/r.md) |
| S | 68 | [S](data/s.md) |
| T | 42 | [T](data/t.md) |
| U | 21 | [U](data/u.md) |
| V | 34 | [V](data/v.md) |
| W | 10 | [W](data/w.md) |
| X | 16 | [X](data/x.md) |
| Y | 7 | [Y](data/y.md) |
| Z | 4 | [Z](data/z.md) |

> 💡 在表格页面中可使用浏览器 `Ctrl+F` 搜索包名。

## ⚠️ 免责声明

兼容性验证结果由 AI 自动验证生成，可能存在部分与实际不符的情况。如发现错误，欢迎 [提交 Issue](https://github.com/ohos-electron/compatible-packages/issues) 反馈。

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
git clone https://github.com/ohos-electron/compatible-packages.git
cd compatible-packages

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
  .trim().split('\n').map(JSON.parse);
```

## 🔧 数据更新

```bash
# 1. 准备新的分析结果 xlsx（sheet「包结论汇总」，含「状态」「包名」「版本」列）
# 2. 运行生成脚本（只收录状态为「通过」的包）
python3 gen_packages.py <xlsx文件路径> --repo ohos-electron/compatible-packages --electron 34
# 3. 提交
git add -A && git commit -m "update: 更新兼容包列表"
git push
```
