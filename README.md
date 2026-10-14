# Event Analysis

Event Analysis 是一套面向具体新闻、事件或聚焦议题的深度分析 Skill。它把事实组装、机制解释、历史参照和一致性检查交给彼此隔离的子代理，再由脚本机械拼接结果，尽量避免同一个分析者用预设结论筛选事实或历史案例。

## 适用范围

适合分析边界清楚、可以核查的事件切片，例如一项政策的具体机制、一个产品的工程取舍或一次公司决策。不适合把整场战争、整次选举或整个产业浪潮一次性当作单一对象；遇到这类问题时，Skill 会先建议缩小范围。

它不用于简单事实查询、普通摘要、预测、投资建议或替用户作出结论。

## 工作流程

1. `fact-assembly` 从多个主体的材料中组装事实，并标明争议和来源局限。
2. `mechanism` 在既有事实之上解释至多两个可迁移的学科机制，不重新调查事实。
3. `historical-reference` 独立寻找历史参照，不读取机制阶段的结论。
4. `consistency-check` 对照机制与历史案例，报告吻合、矛盾或无法核查之处。
5. `scripts/stitch.py` 按固定顺序机械拼接四部分，不改写各阶段内容。

最终分析以中文 Markdown 文件保存；四份中间文件位于隔离的临时目录，并在成品读取后删除。

## 运行条件

- 能够派发相互隔离的子代理；
- 子代理能够检索和核验外部资料；
- 可运行 Python 3；
- 可写入临时目录和用户指定的成品目录。

`scripts/stitch.py` 只使用 Python 标准库，不需要安装第三方依赖。如果运行环境不支持子代理，不应把四个阶段悄悄压缩进同一个上下文，因为这会破坏该 Skill 的隔离设计。

## 仓库结构

```text
event-analysis/
├── SKILL.md
├── agents/
│   ├── fact-assembly.md
│   ├── mechanism.md
│   ├── historical-reference.md
│   └── consistency-check.md
└── scripts/
    └── stitch.py
```

- [`SKILL.md`](SKILL.md)：协调流程、约束和成品规则。
- [`agents/`](agents/)：四个隔离阶段的完整职责说明。
- [`scripts/stitch.py`](scripts/stitch.py)：机械拼接四份阶段产物。

## 许可证

[MIT](LICENSE)
