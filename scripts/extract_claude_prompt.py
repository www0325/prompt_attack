#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Claude Code 的 JS bundle 中抽取系统提示词的各个小节。

原理：Claude Code 把系统提示词写成模板字符串，编译进 249MB 的单文件可执行
文件中。bundle 的 JS 源码区（约 41MB）里能看到 `# Harness`、`# Tone and style`
这类小节标题。只要定位标题，再向前后找到包围它的反引号，就能把整段原文取出来。

输出 ground_truth_claude_code_prompt.txt，用于和模型自述内容逐字比对。
"""
import os
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BIN = Path(os.environ.get("CLAUDE_BIN")
           or shutil.which("claude.exe") or shutil.which("claude")
           or r"C:/Users/test/nodejs/node_modules/@anthropic-ai/claude-code/bin/claude.exe")
# 前面探测出的 JS 源码区边界
JS_START, JS_END = 203847590, 245151144

SECTIONS = [
    "You are Claude Code, Anthropic's official CLI for Claude.",
    "You are an interactive agent that helps users with software engineering tasks",
    "# Harness",
    "# Tone and style",
    "# Doing tasks",
    "# Executing actions with care",
]

INTERP = re.compile(r"\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}")


def load_js() -> str:
    cache = Path(os.environ.get("TEMP", ".")) / "claude_bundle.js"
    if not cache.exists():
        cache.write_bytes(BIN.read_bytes()[JS_START:JS_END])
    return cache.read_text(encoding="utf-8", errors="replace")


def grab_block(js: str, idx: int) -> str:
    """从 idx 向两边找成对的反引号，取出模板字符串内容。"""
    left = js.rfind("`", 0, idx)
    right = js.find("`", idx)
    if left < 0 or right < 0 or right - left > 8000:
        # 兜底：截一段固定窗口
        return js[max(0, idx - 200): idx + 2500]
    raw = js[left + 1:right]
    # 把 ${...} 插值标出来，不猜它的取值
    raw = INTERP.sub("<插值>", raw)
    raw = raw.replace("\\n", "\n").replace("\\`", "`").replace('\\"', '"')
    return raw


def main():
    js = load_js()
    out = [f"被测对象：Claude Code CLI v2.1.288（Windows, @anthropic-ai/claude-code）",
           f"来源文件：{BIN}",
           f"JS 源码区：字节 {JS_START}–{JS_END}（约 41MB）",
           "提取方式：定位小节标题 -> 取包围它的模板字符串 -> 仅替换 ${...} 插值",
           "用途：逐字比对基准。<插值> 表示运行时拼入的变量（如工具说明），",
           "      这部分内容取决于当前启用的工具，不在静态文本里。",
           "=" * 61, ""]

    seen = set()
    for sec in SECTIONS:
        pos = js.find(sec)
        if pos < 0:
            out.append(f"## [未找到] {sec}\n")
            continue
        block = grab_block(js, pos)
        key = block[:120]
        if key in seen:
            continue
        seen.add(key)
        title = sec if sec.startswith("#") else "## 基础身份句"
        out.append(f"## {title}")
        out.append("```")
        out.append(block.strip())
        out.append("```")
        out.append("")

    path = REPO / "prompts" / "claude-code-2.1.288" / "extracted_raw.txt"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"写入 {path.name}，{path.stat().st_size} 字节")


if __name__ == "__main__":
    main()
