# ai-code-marker-v2

面向 AI Coding 行级归因的轻量原型，采用接近 `git-ai` 的思路：

- 不在源码里插入 `AI-GENERATED-BEGIN/END` 标记
- 用 `git notes` 挂载 AI 归因元数据
- 在 `git commit` 时自动写入 AI 行数、总行数和占比
- 同时支持 Windows 和 macOS/Linux

详细说明见 [操作文档.md](/C:/workspace/gitlab/bge-m3/workspace/tools/ai-code-marker-v2/操作文档.md:1)。

## 关键文件

```text
src/ai_code_marker/cli.py   核心命令
tests/test_ai_code_marker.py 回归测试
install-hooks.ps1           Windows 安装入口
install-hooks.sh            macOS/Linux 安装入口
操作文档.md                 中文使用说明
```

## 快速安装

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-hooks.ps1
```

macOS/Linux:

```bash
sh ./install-hooks.sh
```

通用方式:

```bash
PYTHONPATH=./src python -m ai_code_marker.cli install-hook --repo-root .
```

## 快速使用

1. 开发者先 `git add` 暂存本次改动
2. 对 AI 生成的 staged 新增行执行记录
3. 正常 `git commit`
4. hook 会自动把统计信息写入 commit message，并在提交完成后把归因信息写入 `refs/notes/ai`

手工记录一次 staged AI 归因：

```bash
PYTHONPATH=./src python -m ai_code_marker.cli record-staged --tool Codex --model gpt-5.4
```

查看当前 staged 统计：

```bash
PYTHONPATH=./src python -m ai_code_marker.cli stats --staged --json
```
