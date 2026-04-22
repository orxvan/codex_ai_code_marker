# ai-code-marker-v2

面向 AI Coding 行级归因的轻量原型，采用接近 `git-ai` 的思路：

- 在 `git commit` 前自动插入 `AI-GENERATED-BEGIN/END` 标记
- 用 `git notes` 挂载 AI 归因元数据
- 在 `git commit` 时自动写入 AI 行数、总行数和占比
- 同时支持 Windows 和 macOS/Linux

详细说明见 [操作文档.md](/C:/workspace/gitlab/bge-m3/workspace/tools/ai-code-marker-v2/操作文档.md:1)。

## 2026-04-22 更新

- `install-hook` 现在支持给别的 Git 仓库安装，不再只能用于当前工程。
- 生成的 hook 不再写死 `src/ai_code_marker/cli.py` 路径，而是固定使用安装时的 Python 环境执行 `python -m ai_code_marker.cli`。
- 安装后会在 `pre-commit` 自动补 `AI-GENERATED-BEGIN/END` 注释，并自动重新暂存。
- 安装后提交代码时不需要再额外设置 `PYTHONPATH`，也不需要手工先执行 `record-staged`。
- 新增 `range-report`，可按时间范围统计 AI Coding 情况；默认统计从本周一零点到当前时间。

给当前仓库安装：

```bash
python setup.py develop
python -m ai_code_marker.cli install-hook --repo-root .
```

给别的仓库安装：

```bash
python setup.py develop
python -m ai_code_marker.cli install-hook --repo-root /path/to/target-repo
```

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

给别的仓库安装：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-hooks.ps1 -RepoRoot C:\path\to\target-repo
```

macOS/Linux:

```bash
sh ./install-hooks.sh
```

给别的仓库安装：

```bash
sh ./install-hooks.sh /path/to/target-repo
```

通用方式:

```bash
python setup.py develop
python -m ai_code_marker.cli install-hook --repo-root .
```

安装到别的 Git 仓库:

```bash
python setup.py develop
python -m ai_code_marker.cli install-hook --repo-root /path/to/target-repo
```

## 快速使用

1. 开发者先 `git add` 暂存本次改动
2. 正常 `git commit`
3. `pre-commit` 会自动给本次 staged 的 AI 代码块补上 `AI-GENERATED-BEGIN/END`
4. hook 会自动把统计信息写入 commit message，并在提交完成后把归因信息写入 `refs/notes/ai`

安装完成后，hook 会固定使用安装时的 Python 解释器执行 `python -m ai_code_marker.cli`，因此不再依赖目标仓库里的 `src` 目录，也不需要在提交时设置 `PYTHONPATH`。

默认安装的 hook 包括：

- `pre-commit`
- `prepare-commit-msg`
- `post-commit`

手工记录一次 staged AI 归因：

```bash
python -m ai_code_marker.cli record-staged --tool Codex --model gpt-5.4
```

查看当前 staged 统计：

```bash
python -m ai_code_marker.cli stats --staged --json
```

查看时间范围内的 AI Coding 情况：

```bash
python -m ai_code_marker.cli range-report --json
```

指定时间范围和仓库：

```bash
python -m ai_code_marker.cli range-report --repo-root /path/to/repo --since 2026-04-21T00:00:00+08:00 --until 2026-04-22T23:59:59+08:00 --json
```
