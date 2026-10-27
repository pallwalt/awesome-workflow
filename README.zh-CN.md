# Awesome Workflow

[English](README.md)

**给使用 Agent 开发的人准备的一套开发流程，优先适配 Codex 桌面 App。** Awesome Workflow 帮你把新想法或维护需求变成已确定的路线、清楚的验收条件、范围明确的实现、实际验证，以及下次能接着工作的记录。

**0.2.0 候选版**使用公开、未改写的 [Superpowers v7.0.1](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b)，固定提交为 `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`。安装、依赖检查、更新、回滚和移除统一使用仓库工具。已完成的检查与剩余限制见[验证说明](docs/validation.md)；这不代表已经通过真人新手可用性认证。

## 它能帮助你什么

- **新项目先查已有成果。** 同时查找完整替代项目，以及可复用的组件或参考实现，并控制调研范围。
- **把重要取舍讲清楚。** 兼顾复用与差异化，说明推荐及取舍，由你确定整体路线后开始产品实施；已有仍然适用的决定直接沿用。
- **维护任务围绕现有项目。** 从实际代码、相关改动和证据出发，普通修复不必重新做产品调研。
- **交付便于审阅。** 说明改动、必要检查、遗留问题和续接点，保留项目已有内容。

## 开始使用

需要 Git、**Python 3.11 或更新版本**，以及支持符号链接的 macOS 或 Linux 环境。此候选版尚不支持 Windows 安装。

```sh
git clone https://github.com/pallwalt/awesome-workflow.git
cd awesome-workflow
python3 -B scripts/manage.py install
python3 -B scripts/manage.py doctor
```

安装工具下载固定版本的公开 Superpowers 压缩包，核对压缩包指纹及声明资源，再创建唯一的 Awesome Workflow 发现入口。遇到无法确认归属的同名安装会拒绝覆盖；其他技能及客户端配置保持原样。这是 **Awesome Workflow 自己的安装工具**，不是 Superpowers 官方安装器。

安装后，新建 Codex 桌面 App 对话，选择或调用 `awesome-workflow`，说明目标、项目位置，以及需要实施、设计还是审查。例如：

```text
使用 awesome-workflow，帮我做一个虚构的灯会日程编辑器。
在我打开的项目文件夹里工作。先理清最终用途，再比较已有项目和可复用零件，
由我确定整体路线后再实施。
```

干净 Codex App 新会话中的自动发现需单独验收，当前状态见[验证说明](docs/validation.md)。[安装文档](docs/installation.md)提供明确路径调用、离线安装和恢复方式。公开示例与测试输入均为全新虚构，不记录或改写任何人的私有项目。

## 更新与回滚

在适合切换版本的任务间隙，在下载的源码仓库中运行：

```sh
git pull --ff-only
python3 -B scripts/manage.py update
python3 -B scripts/manage.py doctor
```

更新先验证完整的 Awesome Workflow 与 provider 组合，再切换入口，不自动追随 Superpowers 最新分支。如果已有上一套受管理的组合，可以回滚：

```sh
python3 -B scripts/manage.py rollback
python3 -B scripts/manage.py doctor
```

移除受管理入口并保留版本快照：

```sh
python3 -B scripts/manage.py uninstall
```

各操作的归属检查和保留范围见[安装文档](docs/installation.md)。

## 与 Superpowers 如何分工

| 层次 | 负责内容 |
| --- | --- |
| Awesome Workflow | 任务路由、范围、项目与组件选型、适用的用户决定、状态、交付和续接。 |
| Superpowers | 设计、规划、调试、测试、实现、评审与验证的工程方法。 |

Awesome Workflow 从固定安装组合中的 provider 真实目录读取方法，不把同名 Superpowers 方法散装到全局技能目录。未知方法、必需资源缺失、内容漂移或未解决的兼容冲突会阻止受影响阶段。指纹一致只确认内容身份，不证明 Agent 的执行行为正确。

上游更新先作为候选进行审查和验证，再随新的受支持组合发布。你主动更新前，进行中的任务继续使用原组合。详见[兼容规则](skills/awesome-workflow/references/superpowers-compatibility.md)。

## 了解流程与参与贡献

- [Skill 入口](skills/awesome-workflow/SKILL.md)、[选型规则](skills/awesome-workflow/references/open-source-selection.md)与[可选决策卡](skills/awesome-workflow/assets/reuse-decision.md)
- 全新虚构演练：[从零开发](docs/examples/new-project.md)、[维护项目](docs/examples/maintenance.md)、[继续任务](docs/examples/continuation.md)
- [检查器契约](docs/checker-contract.md)、[评测场景](evals/scenarios.md)与[验证限制](docs/validation.md)
- [贡献指南](CONTRIBUTING.md)、[路线图](ROADMAP.md)与[更名说明](RENAME_NOTES.md)

公开仓库不接受私有项目、日志、真实案例摘要或私有经历的改写。报告问题时，请独立编写全新虚构的最小复现。本包命令不上传任务内容或报告。

仓库原创内容采用 [MIT 许可](LICENSE)，另行下载的 provider 及其许可见[第三方说明](THIRD_PARTY.md)。
