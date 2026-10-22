# Claude Code v2.1.288 提示词

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| `extracted_raw.txt` | 按小节抽出的原文，保留 JS 模板字符串上下文 | 本机 `claude.exe`（249MB，Bun 单文件），`scripts/extract_claude_prompt.py` |
| `public_corpus_2.0.txt` | 公开语料中收录的旧版提示词，13,019 字节 | `x1xhlol/system-prompts-and-models-of-ai-tools` |
| `public_corpus_tools.json` | 公开语料中的工具定义 | 同上 |

## 提取方法

提示词不能按字符串直接定位：`You are Claude Code...` 是独立常量，其后紧跟二进制数据。正确做法是先定位 JS 源码区（偏移 203847590–245151144，约 41MB），再按小节标题分别取出包围它的模板字符串，仅替换 `${...}` 插值。

## 注意

- `extracted_raw.txt` 是原始抽取结果，含大量 JS 代码，可直接读的是以 `# Harness`、`# Tone and style`、`# Doing tasks`、`# Executing actions with care` 开头的段落。<插值> 表示运行时拼入的工具说明，不在静态文本里。
- `public_corpus_2.0.txt` 属 2.0 时期结构，无 `# Harness` 与 `# Executing actions with care` 两节。语料收录的是结果，结果天然滞后于版本，比对时须以本地二进制为准。
- 本目录内容版权归 Anthropic 所有，仅作研究引用。
