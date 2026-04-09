# TUI 改进笔记（作为 #62 输入）

> 基于 Textual 最佳实践，对当前 `src/voidcode/tui/` 的 UI/交互问题做的局部记录。

这份笔记**不扩展总体 roadmap**，也不单独定义新的 post-MVP 架构方向。它只作为 **#62「补齐 TUI 对 runtime sessions 与 events 的对齐」** 的实现输入，帮助后续做低冲突的 TUI 整理。

## 使用方式

- 与 `#62` 一起使用，不单独立项
- 优先处理不会改变 runtime protocol 的 TUI 层改动
- 依赖 `#58` 稳定 runtime event protocol 之后，再做更深入的 transcript / rendering 调整

## 建议分层

### A. 可直接纳入 #62 的低风险改进

这些改动基本局限在 `src/voidcode/tui/`，不会改变总体架构边界：

1. **保留终端主题色**
   - `VoidCodeTUI` 增加 `ansi_color = True`
   - `Screen` 增加 `background: transparent`

2. **ApprovalModal 展示更多上下文**
   - 当前审批信息过于简略
   - 应展示更完整的 payload / 参数，帮助用户判断风险

3. **过滤 transcript 中的内部事件**
   - 不是所有 runtime event 都适合直接显示给用户
   - TUI 应只展示用户可理解、可操作的事件层

### B. 应在 #58 之后推进的改进

这些改动高度依赖稳定后的 runtime event vocabulary / session truth，过早推进容易返工：

1. **Transcript 事件分层显示**
   - 用户消息
   - 工具调用
   - AI 输出
   - 审批请求/决策

2. **AI 输出改为更合适的渲染组件**
   - Markdown / MarkdownStream
   - 需要和实际 runtime 输出节奏匹配

3. **状态区去重与布局整理**
   - 删除 `#current-response` 的冗余状态表达
   - 将状态统一到更稳定的位置（Header / Footer / Sidebar）

### C. 应谨慎评估、不要抢先做的改动

这些建议有价值，但会扩大 TUI 改动面，不应在 #62 初次落地时抢占优先级：

1. **用 `reactive` 全面替代当前状态同步方式**
   - 可能带来较大重构面
   - 更适合在 TUI 基础交互稳定后再做

2. **Input / transcript / sidebar 的整体布局重排**
   - 有助于体验，但不是当前与 runtime 对齐的核心阻塞项

## 推荐的 #62 执行顺序

1. 先消费稳定的 runtime session / event 语义
2. 再做低风险 TUI 展示修正
3. 最后再评估是否引入更大规模的组件/状态重构

## 结论

这份笔记的价值在于帮助 `#62` 避免盲目改 UI。

但它不应该抢在 `#58` 前面，也不应该演变成一份新的总体设计文档。当前最正确的定位是：**#62 的局部实现输入与参考清单。**
