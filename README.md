# electron-compatible-packages

已在鸿蒙 PC 的 Electron 34 上验证通过的 npm 包列表。这些包可直接在该 Electron 环境中使用，无需额外适配。

## 📊 统计摘要

> 更新日期：2026-10-29 | 兼容包总数：**227**

## 🔍 在线查询

👉 **[点击打开搜索页](https://shizishizi.github.io/electron-compatible-packages/)**（支持按包名搜索 + 按字母浏览）

**按字母浏览**（GitHub Markdown 表格）：

| 字母 | 包数量 | 浏览表格 |
|------|--------|---------|
| A | 12 | [A](data/a.md) |
| B | 12 | [B](data/b.md) |
| C | 13 | [C](data/c.md) |
| D | 13 | [D](data/d.md) |
| E | 15 | [E](data/e.md) |
| F | 8 | [F](data/f.md) |
| G | 7 | [G](data/g.md) |
| H | 6 | [H](data/h.md) |
| I | 9 | [I](data/i.md) |
| J | 9 | [J](data/j.md) |
| K | 1 | [K](data/k.md) |
| L | 11 | [L](data/l.md) |
| M | 16 | [M](data/m.md) |
| N | 7 | [N](data/n.md) |
| O | 2 | [O](data/o.md) |
| P | 12 | [P](data/p.md) |
| Q | 4 | [Q](data/q.md) |
| R | 10 | [R](data/r.md) |
| S | 16 | [S](data/s.md) |
| T | 10 | [T](data/t.md) |
| U | 7 | [U](data/u.md) |
| V | 9 | [V](data/v.md) |
| W | 4 | [W](data/w.md) |
| X | 10 | [X](data/x.md) |
| Y | 2 | [Y](data/y.md) |
| Z | 2 | [Z](data/z.md) |

> 💡 在表格页面中可使用浏览器 `Ctrl+F` 搜索包名。

## ⚠️ 免责声明

兼容性验证结果由 AI 自动验证生成，可能存在部分与实际不符的情况。如发现错误，欢迎 [提交 Issue](https://github.com/ShiZiShiZi/electron-compatible-packages/issues) 反馈。

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
git clone https://github.com/ShiZiShiZi/electron-compatible-packages.git
cd electron-compatible-packages

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
python3 gen_packages.py <xlsx文件路径> --repo ShiZiShiZi/electron-compatible-packages --electron 34
# 3. 提交
git add -A && git commit -m "update: 更新兼容包列表"
git push
```
