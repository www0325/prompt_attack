#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从单文件二进制中提取系统提示词原文（作为逐字比对基准）。

用途：OpenCode / Claude Code 都是把 JS 源码编译进单个可执行文件的，
系统提示词以字符串常量形式存在于其中。只要给出一个"锚点句"和一个
"终止标记"，就能把整段 prompt 原样切出来。

这不是攻击，是读自己机器上的文件——但它是验证"模型输出是否为编造"
的唯一硬证据。

用法：
    python extract_ground_truth.py opencode
    python extract_ground_truth.py claude
    python extract_ground_truth.py all
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def find_bin(env, exe, default):
    return os.environ.get(env) or shutil.which(exe) or default

TARGETS = {
    "opencode": {
        "path": find_bin("OPENCODE_BIN", "opencode.exe",
                         r"C:/Users/test/nodejs/node_modules/@opencode/cli/bin/opencode.exe"),
        "anchor": "You are an AI agent running in OpenCode, a coding agent harness.",
        # 提示词内部的小节标题，用于确定结尾
        "stop_markers": ["Create a plan", "Title Generation", "\n\nYou are a", "MZ@"],
        "max_len": 12000,
        "out": "prompts/opencode-2.0.28/identity_block.txt",
    },
    "claude": {
        "path": find_bin("CLAUDE_BIN", "claude.exe",
                         r"C:/Users/test/nodejs/node_modules/@anthropic-ai/claude-code/bin/claude.exe"),
        "anchor": "You are Claude Code, Anthropic's official CLI for Claude.",
        "stop_markers": ["MZ@", "This is a reminder", "\x00\x00\x00"],
        "max_len": 20000,
        "out": "prompts/claude-code-2.1.288/extracted_raw.txt",
    },
}

# 单文件 JS 会被压成一行，换行是字面量 \n 两个字符。判"可读"时只保留
# 中英可见字符与常见标点，其余一律视为二进制噪声。
KEEP = re.compile(r"[0-9A-Za-z\u4e00-\u9fff \t\r\n`~!@#$%^&*()\-_=+\[\]{}|\\;:'\",.<>/?]")
ESCAPED_NL = re.compile(r"\\n")


def readability(chunk: str) -> float:
    if not chunk:
        return 0.0
    good = sum(1 for ch in chunk if KEEP.match(ch))
    return good / len(chunk)


def walk_from(blob: bytes, start: int, max_len: int):
    """从 start 开始，逐段前行直到可读性崩塌（说明进入二进制数据区）。"""
    out = []
    pos = start
    step = 400
    while pos < len(blob) and sum(len(x) for x in out) < max_len:
        raw = blob[pos:pos + step]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        if readability(text) < 0.93:
            # 允许一点点噪声，但随后要停
            if readability(text) < 0.80:
                break
        out.append(text)
        pos += step
    return "".join(out)


def extract(name: str) -> Path:
    cfg = TARGETS[name]
    path = Path(cfg["path"])
    if not path.exists():
        raise SystemExit(f"找不到文件：{path}")

    blob = path.read_bytes()
    anchor = cfg["anchor"].encode("utf-8")
    idx = blob.find(anchor)
    if idx < 0:
        raise SystemExit(f"{name}: 未找到锚点句")

    text = walk_from(blob, idx, cfg["max_len"])

    # 压平字面量换行，便于阅读与 diff
    text = ESCAPED_NL.sub("\n", text)

    # 截到停止标记
    end = len(text)
    for m in cfg["stop_markers"]:
        p = text.find(m)
        if p > 200:
            end = min(end, p)
    text = text[:end].rstrip()

    # 去掉尾部仍是二进制噪声的行
    lines = text.split("\n")
    while lines and readability(lines[-1]) < 0.95:
        lines.pop()
    text = "\n".join(lines)

    header = (
        f"被测对象：{name}\n"
        f"来源文件：{path}\n"
        f"字节偏移：{idx}\n"
        f"提取方式：锚点句定位 + 可读性截断（非模型输出，是文件内容）\n"
        f"用途：仅作逐字比对基准，证明模型输出并非编造\n"
        + "=" * 57 + "\n\n"
    )
    out = REPO / cfg["out"]
    out.write_text(header + text + "\n", encoding="utf-8")
    print(f"[{name}] 偏移 {idx}，提取 {len(text)} 字符 -> {out.name}")
    return out


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(TARGETS) if arg == "all" else [arg]
    for n in names:
        try:
            extract(n)
        except SystemExit as e:
            print(f"[{n}] 跳过：{e}")
    print(json.dumps({"done": names}, ensure_ascii=False))


if __name__ == "__main__":
    main()
