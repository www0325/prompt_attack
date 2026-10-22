# OpenCode v2.0.28 身份句与 Harness 小节

`identity_block.txt` 是从 `opencode.exe` 中取出的 755 字符对照文本，包含身份句与 `# Harness` 小节的头几条规则。它是本实验判定 OpenCode 组「逐字级成功」的基准。

## 位置

身份句在二进制中命中两次：

- 偏移 198,642,294
- 偏移 212,302,724

两处内容一致，说明二进制里存在长短两个版本：第二处长版本还带有 `# Your Model`、Code Mode 工具目录与 skill 清单，第二轮实验中 doubao-seed-2-0-mini 一次直接索取吐出的 15,480 字节正是这一版。

## 提取

```bash
python scripts/extract_ground_truth.py
```

脚本按特征句在 `opencode.exe` 中检索并截取上下文，输出到 `ground_truth_opencode_prompt.txt`。

版权归 OpenCode 项目所有，仅作研究引用。
