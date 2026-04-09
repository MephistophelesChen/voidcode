# 架构改进笔记（归档）

> 参考来源：Claude Code (`claude-code-source-code`)、oh-my-opencode

这份笔记最初用于整理外部实现中的可借鉴点。其核心建议已经被提炼并合并到主设计文档，不再作为独立的长期维护规划文档继续展开。

## 已提炼去向

以下内容已经并入 `docs/post-mvp-technical-design.md` 的“补充架构改进优先级”部分：

- Context Window 管理
- Provider fallback chain 与错误分类
- `max_steps` 可配置
- 从同步 `Iterator` 向异步流执行模型演进
- 并发工具执行
- 工具动态加载 / 插件式发现
- 会话事件日志增长控制
- 进程内 Hook
- MCP 集成
- 重新评估 LangGraph 的必要性

## 当前用途

本文件仅保留为来源记录与归档索引，用于说明这些建议的参考背景，不再单独维护详细优先级、分阶段建议或重复的架构结论。

后续若要落地相关改进，请以以下文档为准：

- `docs/post-mvp-technical-design.md`
- `docs/roadmap.md`
- 对应 GitHub issues / pull requests
