"""从 opencode.exe 中导出系统提示词原文，作为逐字比对基准。"""
import os
import re
import shutil
from pathlib import Path

BIN = Path(os.environ.get("OPENCODE_BIN")
           or shutil.which("opencode.exe") or shutil.which("opencode")
           or r"C:/Users/test/nodejs/node_modules/@opencode/cli/bin/opencode.exe")
OUT = (Path(__file__).resolve().parent.parent
       / "prompts" / "opencode-2.0.28" / "identity_block.txt")

data = BIN.read_bytes()
needle = b"You are an AI agent running in OpenCode"
idxs = [m.start() for m in re.finditer(re.escape(needle), data)]
print("二进制中命中次数：", len(idxs))

if not idxs:
    raise SystemExit("未找到，可能版本已变")

# 取最长的一段（含后文最多的那个）
best = max(idxs, key=lambda i: len(data[i:i + 6000]))
seg = data[best: best + 4000].decode("utf-8", errors="replace")
# 丢弃不可打印与二进制噪声，保留基本文本
seg = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u4e00-\u9fff]", "", seg)

OUT.write_text(
    "被测对象：OpenCode CLI（开源，dev 版二进制）\n"
    "提取位置：@opencode/cli/bin/opencode.exe 偏移 %d\n"
    "提取方式：按字符串定位后截取，非完整 prompt，仅作逐字比对基准\n"
    "=========================================================\n\n" % best + seg[:2500],
    encoding="utf-8")

print("已保存：", OUT)
print("\n----- 前 900 字 -----")
print(seg[:900])
