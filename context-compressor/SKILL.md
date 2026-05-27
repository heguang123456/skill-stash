---
name: context-compressor
description: 上下文压缩与交接班日志生成。将冗长的每日开发日志压缩为结构化的项目状态文档。触发条件：用户提到交接班、压缩记忆、归档、生成STATUS、handoff、compress 等关键词，或在完成里程碑时主动建议归档。核心能力：滚动窗口断代压缩（热数据保留在 docs/STATUS.md，100-150行，里程碑归档到 CHANGELOG.md）；带注释的目录树快照替代行数统计；注意力锚点机制（按需拆分为 vibe_status.md, vibe_todo.md, vibe_architecture.md）。
agent_created: true
---

# Context Compressor — 上下文压缩与交接班日志

## 目的

在 vType 项目的开发过程中，每日日志（`.workbuddy/memory/YYYY-MM-DD.md`）和状态文档会不断累积。
每次新会话开始时，大量历史细节会占据 AI 的上下文窗口，降低效率。

Context Compressor 实现"滚动窗口 + 断代压缩"策略：
- **热数据**：当前活跃的开发状态保持在 `docs/STATUS.md`（100-150 行以内）
- **冷数据**：已完成的里程碑高度压缩后归档到 `CHANGELOG.md`
- **结构性输出**：用带注释的目录树替代精细的行数统计
- **注意力锚点**：按需拆分为三份独立文件，只喂给 AI 需要的部分

## 触发条件

在以下任一情况发生时，执行压缩流程：

1. 用户明确说"交接班""压缩记忆""归档""生成STATUS""handoff""compress""sync-status"
2. 当前版本的 9 个模块全部标记为完成（Milestone 收尾）
3. `.workbuddy/memory/` 下有超过 7 天的每日日志
4. 新会话开始时，上次压缩距今超过 5 天

## 工作流程

### Step 1: 采集阶段 — 收集所有源数据

并行读取以下文件：

- `.workbuddy/memory/MEMORY.md` — 项目长期记忆
- `.workbuddy/memory/YYYY-MM-DD.md` — 最近 30 天内的每日日志
- `CHANGELOG.md` — 现有里程碑记录
- `README.md` — 项目说明
- `requirements.txt` / `requirements-dev.txt` — 依赖清单

执行 `scripts/generate_tree_snapshot.py` 获取带注释的目录树快照。

### Step 2: 压缩阶段 — 断代压缩每日日志

对每日日志按时间分类：

- **热窗口（最近 3 天）**：保留完整细节，不做压缩
- **温窗口（4-7 天前）**：提取关键决策和修复（Bug 修复、设计决策、技术陷阱），丢弃过程性流水
- **冷窗口（8-30 天前）**：高度压缩为一段话，归档到 CHANGELOG.md
- **过期（30 天以上）**：如果已归档到 CHANGELOG.md，删除每日日志文件

对冷窗口日志的压缩规则参考 `references/compression_rules.md`。

**关键原则**：
- 不要逐日归档每一个"今日已修"细节
- 将同一 Milestone 内的多条日志合并为一段高度概括的叙述
- 只保留：架构决策、重要 Bug 修复、模块完成标记、技术陷阱发现
- 丢弃：临时的调试过程、单文件的小修改、routine 类型操作

### Step 3: 生成阶段 — 撰写 docs/STATUS.md

从 MEMORY.md 和最近的每日日志中提取，按以下固定结构生成：

```markdown
# vType 项目状态

## 版本信息
当前版本 / 分支 / 最后更新日期

## 核心指标
状态：开发中 / 测试中 / 可发布
代码总行数 / 测试总数 / 测试通过率
关键里程碑完成度（进度条）

## 当前任务（TODO）
[ ] 正在进行的任务（不超过 5 项）
[ ] 等待修复的 Bug

## 目录树快照
（由 generate_tree_snapshot.py 生成，带模块职责注释）

## 最近变更（最近 3 天）
关键变更（一句话每条，不超过 5 条）

## 已知风险
需要注意的技术陷阱或待解决问题
```

使用 `assets/templates/status_template.md` 作为格式模板。**严格控制不超过 150 行**。

### Step 4: 归档阶段 — 更新 CHANGELOG.md

如果当前版本所有模块标记为完成：
1. 将 MEMORY.md 中"实现进度"表格的内容转换为 Changelog 条目
2. 提取压缩后的关键修复和优化信息
3. 在 CHANGELOG.md 中创建新版本条目（遵循 Keep a Changelog 格式）
4. 更新 MEMORY.md 中"实现进度"表格为下一版本占位

### Step 5: 拆分阶段（可选）— 注意力锚点

当用户指定"只贴 TODO"或"只发架构"等需求时，将 STATUS.md 拆分为三个文件：

- `docs/vibe_status.md` — 版本信息 + 核心指标（5-10 行）
- `docs/vibe_todo.md` — 当前任务 + 已知风险（10-20 行）
- `docs/vibe_architecture.md` — 目录树快照 + 技术栈（基本不动，20-40 行）

拆分采用文件末尾注释标定边界的方式：

```markdown
<!-- SPLIT: status | todo | architecture -->
```

### 完成与清理

1. 标记本次压缩的日期
2. 输出压缩摘要：删除/归档了多少条日志、STATUS.md 行数、Changelog 新增条目
3. 建议是否需要将 `.workbuddy/memory/` 中超过 30 天的日志文件清理
4. 将本次压缩操作记录到当天的每日日志中
