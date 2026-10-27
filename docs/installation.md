# Installation, updates, and recovery / 安装、更新与恢复

This document describes Awesome Workflow's managed installation for the **0.2.0 candidate**, targeting Codex desktop App on macOS/Linux. It uses Python 3.11+ and Git; no third-party Python packages are required. Windows, other clients, and clean App discovery have separate validation boundaries in [validation](validation.md).

本文适用于 macOS/Linux 上、以 Codex 桌面 App 为目标的 **0.2.0 候选版**。需要 Python 3.11+ 和 Git，无需额外 Python 包。Windows、其他客户端及干净 App 自动发现的验证边界分别见验证说明。

## 1. Install / 安装

```sh
git clone https://github.com/pallwalt/awesome-workflow.git
cd awesome-workflow
python3 -B scripts/manage.py install
python3 -B scripts/manage.py doctor
```

For `install` and `update`, the default source is the repository containing `scripts/manage.py`; `--source` can select another reviewed package root. `doctor` reads only the installed state and does not require the source checkout. `--home` defaults to the current user's home; supply an isolated temporary directory when testing installation behavior. Add `--json` for structured output.

`install` 与 `update` 默认使用 `scripts/manage.py` 所在仓库，`--source` 可另选已审阅的包根目录。`doctor` 只读已安装状态，不依赖原源码目录。`--home` 默认使用当前用户主目录，测试时应指定独立临时目录；加 `--json` 可取得结构化结果。

Installation prepares and validates a versioned package/provider combination before exposing one entry:

```text
~/.local/share/awesome-workflow/
  releases/<combination-id>/
    package/
    superpowers/
  ...managed ownership and version state...
~/.agents/skills/awesome-workflow -> managed combination's skill
```

`install`, `update`, `rollback`, and `uninstall` move an owned install from the previous product directory onto these paths. `doctor` only reads the directory it finds and does not rename it. If both data directories exist, or the previous skill entry is not an owned symlink, the command stops and preserves them. See [rename notes](../RENAME_NOTES.md).

`install`、`update`、`rollback` 和 `uninstall` 会把仍能确认归属的上一产品目录安装迁到这些路径。`doctor` 只读取找到的目录，不改名。若两个数据目录同时存在，或旧技能入口不是受管理的符号链接，命令会停止并保留原内容。详见[更名说明](../RENAME_NOTES.md)。

The exact combination ID is managed by the tool. Provider method files retain their upstream bytes in `superpowers/`; the controller resolves methods from that physical directory. The tool does not install each provider method as a global skill, alter other client configuration, or replace unrelated skills.

安装先准备并验证完整版本组合，再暴露入口。provider 文件保留上游原始字节，方法从组合内真实目录读取；工具不把所有方法逐一安装成全局技能，不修改其他客户端配置或无关技能。

**An existing unrecognized same-name entry is a stop condition.** The tool will not adopt, delete, rename, or overwrite it. Inspect its origin and preserve it before deciding a separate migration. Do not remove an existing skill merely to make the command pass.

**无法确认归属的同名入口会阻止安装。** 工具不接管、不删除、不改名、不覆盖。先核实来源并保留现有内容，再另行决定迁移；不要为了让命令通过而直接删掉已有技能。

## 2. Verify and start a task / 检查与开始任务

`doctor` checks the managed entry, recorded package, provider resources, and ownership. A success establishes the checked installation state. It does not prove Codex has loaded the skill, that a model will obey it, or that a project is complete.

`doctor` 检查受管理入口、包、provider 资源及归属。成功仅说明这些安装状态通过检查，不证明 App 已加载、模型必然遵循，或项目已经完成。

Start a **new** Codex desktop App conversation after installation or a version switch. Select/invoke `awesome-workflow`, describe the goal and target project, and specify the scope. If it is not listed, give the agent the installed skill's absolute path. Replace placeholders before using this instruction:

```text
Read [absolute home directory]/.agents/skills/awesome-workflow/SKILL.md
and use it for this task. Resolve its managed provider and check the dependency
before a dependent stage. Goal: [desired outcome]. Project: [authorized folder].
Scope: [implementation, design only, or read-only review].
```

If discovery is unavailable, explicit-path loading is a fallback with its own evidence scope; it is not proof of automatic discovery. Do not bypass a failed dependency check. Real user direction decisions still precede new-product implementation; an applicable decision already supplied by the user can be reused.

如未自动发现，可使用明确路径调用，但不能将其记作自动发现成功，也不能绕过依赖失败。新产品实施前仍需真实的整体路线决定，已有适用决定可沿用。

## 3. The pinned dependency / 固定依赖

The candidate binds to official [Superpowers v7.0.1](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b), commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`. The [profile](../skills/awesome-workflow/references/superpowers-profile.json) declares required methods, files, and hashes. The installer normally obtains that public archive and checks it before activation; it does not download a private customization.

候选版固定使用上述官方公开提交，必需方法、文件及指纹由 profile 声明。安装器默认下载公开压缩包并检查，不读取或分发私有定制依赖。

For offline installation, obtain the same official revision from a trusted source first, then supply its extracted root:

```sh
python3 -B scripts/manage.py install --provider-source /absolute/path/to/public-superpowers
python3 -B scripts/manage.py doctor
```

This mode verifies the **declared resources only**. It does not authenticate the origin or every other file in the supplied directory. Matching filenames or a directory called `superpowers` is insufficient. Content matching is identity evidence; behavior remains bounded by the published validation results.

本地目录模式只核验 **profile 声明的资源**，不证明目录整体来源或其他文件身份。同名目录或文件不足以判定兼容；指纹也不等于行为证据。

For the stronger full-archive identity check offline, supply the original pinned official tar archive instead:

```sh
python3 -B scripts/manage.py install --provider-archive /absolute/path/to/superpowers.tar.gz
python3 -B scripts/manage.py doctor
```

Both the default download and `--provider-archive` verify the pinned archive SHA-256 as well as the declared extracted resources. Use either `--provider-source` or `--provider-archive`, not both. The same provider options are available for `update`.

默认下载与 `--provider-archive` 均核对固定压缩包整体 SHA-256 及声明资源。两项 provider 参数只能选一项，`update` 也支持相同参数。

The upstream project currently documents its own installation mechanisms, including Codex plugin distribution. This managed layout is Awesome Workflow's distribution choice for a pinned combination; it is not an upstream installer or a replacement for upstream installation advice. Read [third-party notices](../THIRD_PARTY.md) and [compatibility rules](../skills/awesome-workflow/references/superpowers-compatibility.md).

For online downloads the tool uses system `curl` when available, with a Python
standard-library HTTP fallback. It installs neither downloader. Transfers are
bounded and must match the pinned complete archive digest; a truncated or wrong
download is rejected. A blocked network can use `--provider-archive` instead.

在线下载优先使用系统已有的 `curl`，否则使用 Python 标准库 HTTP；工具不会安装下载器。
传输有次数与时间限制，完整压缩包必须匹配固定指纹，截断或错误内容不会被放行。
网络受阻时可提供上述离线压缩包。

## 4. Update / 更新

Finish or hand off the current task before changing its dependency combination. In the downloaded source repository:

```sh
git pull --ff-only
python3 -B scripts/manage.py update
python3 -B scripts/manage.py doctor
```

Review the source changes and release's validation before updating. If the checkout has conflicting local edits, resolve them without discarding work. The update validates the new package and fixed provider before switching the managed entry. A failed validation must leave the previous entry active. Re-running against the same combination does not require inventing a new dependency version.

先审阅源码变化及验证范围。若源码目录有冲突或本地修改，应保留并处理，不能为更新丢弃。新组合验证失败时，旧入口继续有效；相同组合重复操作不应凭空升级依赖版本。

Superpowers updates do not mutate an installed combination. Maintainers review upstream candidates, adjust declared compatibility where justified, run the relevant checks, and ship a new combination. Changing only a hash to suppress drift is not compatibility work.

## 5. Roll back / 回滚

When a previous managed combination exists:

```sh
python3 -B scripts/manage.py rollback
python3 -B scripts/manage.py doctor
```

Rollback validates the saved combination and switches Awesome Workflow **and** its provider together. It does not change your project files or undo generated code. A missing, changed, or unowned saved combination is not safe to activate and must be reported. Start a new App conversation after a successful switch.

回滚会验证已保存组合，再整体切换 Awesome Workflow 与 provider。它不撤销项目代码；缺失、已变更或归属不明的旧组合不能激活。切换成功后新建 App 对话。

## 6. Uninstall / 移除

```sh
python3 -B scripts/manage.py uninstall
```

This removes only an entry whose ownership still matches the managed record. Version snapshots remain for inspection and recovery; it is not a disk-cleanup command. An independently changed entry must not be removed. Other skills, client settings, and project files remain outside this operation.

仅移除仍能确认归属的受管理入口，保留版本快照；这不是清理磁盘的命令。被独立改动的入口不得移除，其他技能、客户端设置及项目文件不在操作范围内。

## Troubleshooting / 常见问题

The manager serializes its own operations and records recoverable transitions.
Entry replacement may have a brief absence window. If another process creates or
changes the entry during a transition, preserve that content and inspect `doctor`'s
recovery report; do not force replacement. The source inventory is a content
manifest, not a digital signature: obtain it and the manager from a trusted,
reviewed release. Keep extra local notes outside the immutable source package.

管理器会串行执行自身操作，并记录可恢复的切换过程；切换时入口可能短暂缺席。
若其他进程同时改动入口，应保留其内容并检查 `doctor` 的恢复报告，不强行覆盖。
源码清单是内容指纹而非数字签名，应从可信、已审阅的版本获取；额外笔记请留在源码包外。

| Result | Next step |
| --- | --- |
| Unrecognized existing entry | Inspect and preserve it; do not force ownership or delete it to bypass the check. / 核实并保留，勿强行接管或删除。 |
| Source history diverges during pull | Preserve edits and clone into a new directory; do not reset or clean the existing checkout. / 保留改动并克隆到新目录，不重置或清空旧目录。 |
| Provider download unavailable | Retry the same public source later, or supply the verified public revision with `--provider-source`. / 稍后重试同一公开源，或提供已核对的离线目录。 |
| Missing or drifted resource | Keep the task before its affected stage; inspect the report and restore the supported combination. / 停在受影响阶段前，按报告恢复支持的组合。 |
| No previous combination | Rollback is unavailable; do not pretend that a first install has an older version. / 首次安装没有上一组合，不能伪称已回滚。 |
| App does not list the skill | Start a new conversation and use the explicit path if needed; record discovery as unverified. / 新建对话，必要时明确路径调用，发现状态仍需实测。 |

All commands act locally apart from the declared public dependency download. They do not upload task data, local logs, or installation reports. Public bug reports should use newly invented independent reproductions, as explained in [CONTRIBUTING.md](../CONTRIBUTING.md).
