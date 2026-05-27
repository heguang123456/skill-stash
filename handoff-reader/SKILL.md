---
name: handoff-reader
description: 交接日志读取器。在每次新会话开始时读取 docs/STATUS.md，快速恢复项目状态上下文。触发条件：用户提到"交接班""项目状态""完成情况""handoff""项目进展""status"等关键词，或在 vType 项目会话开始时主动加载。
agent_created: true
---

# Handoff Reader — 交接日志读取器

## 目的

vType 项目的交接日志 `docs/STATUS.md` 是跨会话上下文的核心载体。
Handoff Reader 在新会话开始时读取 STATUS.md，让 AI 在最少 token 消耗下快速恢复项目状态全貌。

## 触发条件

在以下任一情况发生时，执行读取流程：

1. 新会话开始时（vType 项目会话的首次任务）
2. 用户说"交接班""看下项目状态""项目进展""完成情况""handoff""status"
3. 用户询问"当前还有哪些待办""最近改了什么""有什么风险"
4. 准备开始新的开发任务前，需要了解当前项目全貌

## 工作流程

### Step 1: 读取交接日志

读取 `docs/STATUS.md`（约 100 行），获取以下信息：

- 版本信息与分支状态
- 核心指标（模块完成度、测试通过率、代码量）
- 当前待办任务（TODO）
- 最近变更记录
- 已知风险与跟踪状态

### Step 2: 读取长期记忆

读取 `.workbuddy/memory/MEMORY.md`，获取项目约定、技术栈、架构设计等长期信息。

### Step 3: 读取最近每日日志

读取 `.workbuddy/memory/` 下最近 3 天的每日日志，了解最新的开发细节。

### Step 4: 输出状态摘要

以结构化方式向用户汇报当前项目状态：版本、完成度、待办数量、风险数量。

## 输出格式

```markdown
## vType 项目状态摘要

- **版本**：vX.Y.Z | **分支**：BRANCH | **状态**：STATUS
- **模块**：N/9 完成 | **测试**：N passed | **通过率**：XX%
- **待办**：N 项 | **风险**：N 项（高: M, 中: K, 低: J）
```

## 注意事项

- 本 skill 只读不写，不会修改任何文件
- STATUS.md 的行数控制在 150 行以内，读取成本极低
- 如需更新 STATUS.md，使用 `context-compressor` skill
- 如果 STATUS.md 的最后更新距今超过 5 天，提示用户运行 context-compressor 刷新
