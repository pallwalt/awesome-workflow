# Validation and evidence limits / 验证与证据边界

This page records the acceptance status of the **0.2.0 candidate**. Only fresh fictional fixtures and independent synthetic tasks may be used for public validation. No real project, personal case, task log, or rewritten summary of private activity is a source for this page.

本页记录 **0.2.0 候选版**的验收状态。公开验证只能使用全新虚构样例和独立合成任务，不使用真实项目、个人案例、运行日志或私有经历的改写摘要。

## Acceptance ledger / 验收记录

`Pending` means a check has not yet produced reviewable evidence for this candidate. A planned scenario or an expected result is not a pass. Maintainers must replace entries only with results from the exact package/provider combination and public synthetic inputs under review.

`Pending` 表示本候选版尚未取得可审阅证据。计划和预期不能记为通过；只有对应被测组合与公开合成输入的实际结果才能更新下表。

| Area | Status | What a pass would establish |
| --- | --- | --- |
| Package, links, profile schema, and failure cases | Passed locally | Package and official metadata validators passed; 80 tool tests passed (38 checker, 42 lifecycle). |
| Pinned public provider provenance and required bytes | Passed | Official archive digest and 55 declared resources match v7.0.1; content identity only. |
| Install and doctor in an isolated temporary home | Passed locally | Both downloaded and offline official archives installed and passed doctor in separate temporary homes. |
| Update failure preservation and unknown-entry rejection | Passed in synthetic tests | Unknown entries, changed snapshots, interrupted transfers, corruption and concurrent entry changes are rejected or retained for recovery. |
| Whole-combination update, rollback, and uninstall | Passed locally | A synthetic package-version transition using the real official provider switched, rolled back and uninstalled, retaining both snapshots. |
| Independent fictional task behavior | Focused observations passed | Four fresh native-agent tasks; implementation acceptance 6/6 and 4/4, selection artifact checks 2/2 each plus controller process review. See limits below. |
| Fresh Codex desktop App conversation on an existing macOS profile | Passed locally | The conversation catalog discovered the managed skill; name-only invocation loaded the pinned provider and completed the fictional maintenance and offline decision tasks. See the App acceptance scope below. |
| GUI skill picker and clean-machine/profile setup | Pending | Neither direct GUI selection nor a clean machine/profile was exercised. Existing-profile conversation discovery does not establish these results. |
| First-time human usability | Not evaluated | Requires a separate consented study using purpose-made fictional tasks. |
| Comparison with Superpowers alone | Not evaluated | Requires a declared comparable protocol and observed results. |
| Other clients and Windows installation | Not supported by this candidate | Requires separate installation, discovery, and behavior acceptance. |

## Reproduce package checks / 复现包检查

From the reviewed repository root, with Python 3.11 or newer:

```sh
python3 -B scripts/check.py --package-root . --json
python3 -B -m unittest discover -s tests -v
```

The [checker contract](checker-contract.md) describes each status. Without an explicit provider root, provider availability is `not_checked`. When exercising a public extracted provider separately:

```sh
python3 -B scripts/check.py --package-root . --provider-root /absolute/path/to/public-superpowers --json
```

`content_match` identifies declared file bytes. It does not change `behavioral_status: not_certified`. Unit tests verify the tools' specified behavior; they do not measure an agent's project success rate.

`content_match` 只确认声明文件的字节身份，不能把 `behavioral_status: not_certified` 改写为行为认证。工具单元测试也不能替代 Agent 项目成功率。

## Observed synthetic run scope / 本轮合成验证范围

Validation used Python 3.13.2 on macOS arm64 and native Codex subagents, loading the candidate by explicit path with the pinned provider. Model settings were inherited; a fixed model build was not independently recorded. This is a focused smoke evaluation, not a controlled benchmark.

| Newly fictional case | Actual observation | Limit |
| --- | --- | --- |
| Museum catalog maintenance | External acceptance 6/6; distinct catalog identities preserved; protected fictional note/settings unchanged; worker reported 10 passing tests after a failing reproduction. | No browser or independent worker-dispatched review. Controller checked the output interface and artifacts. |
| Approved command continuation | External acceptance 4/4; worker reported 14 tests; supplied route reused without another route approval. | Approval was explicit synthetic input, not evidence of a historical conversation. |
| New project selection | Two focused research rounds; three repositories total across full tools and parts; evidence levels separated; user route awaited. Artifact gates 2/2 and controller rubric review passed. | Candidates were not cloned, installed or run. Artifact checks alone do not prove research quality. |
| Offline selection | Both research tracks explicitly unperformed; no candidates invented, network used or code implemented. Artifact gates 2/2 and controller rubric review passed. | Research and product completion remain pending the route decision. |

No corrective controller follow-up was sent during these four runs. Workers could not spawn further agents; their final responses disclosed the unavailable independent review. Public results above summarize only these newly invented tasks; raw dialogues and machine receipts stay private.

Installation testing initially exposed truncated Python HTTP downloads. They were rejected without activating a package. The tested manager now prefers existing system curl and verifies the complete pinned archive; online and offline integration then passed. The HTTP fallback has simulated success/failure tests, but its live transfer remained unreliable in this environment. Three independent safety findings were repaired and checked: concurrent entry preservation, extraction from already verified bytes, and prompt rejection of FIFO files.

这些结果只描述本轮全新虚构输入。独立入口验收不等于真人可用性或整体认证；原始对话与机器回执不公开。CI runs are independently inspectable on the pull request and are not implied by a local pass.

## Codex desktop App acceptance — 2026-10-24 / 桌面 App 实测

The managed installer and doctor passed against an actual macOS user skill root.
A fresh local conversation created through Codex desktop App found
`dumbcane-workflow` in its own skill catalog. The request supplied the skill name,
not an absolute skill or provider path. The agent resolved the managed combination,
matched all 55 pinned provider resources and read the official methods from that
combination. The environment was App 26.1021.31345 (build 21828), macOS arm64,
Python 3.13.2, with the inherited model identifier `gpt-6-astra` and effort `ultra`;
a fixed model build was not independently recorded.

| Purpose-made fictional task | Actual result |
| --- | --- |
| Museum maintenance, fresh staged copy | Four new regression failures before the repair; 10 ordinary/regression tests after the repair; external interface acceptance 6/6. Five protected or original files retained their exact bytes. |
| Offline selection, separate task in the same conversation | Artifact gates 2/2 and independent process review passed. Both research tracks were explicitly unperformed; no candidates, network calls or product code were invented, and the route remained undecided. The earlier maintenance approval was not reused as a new-project decision. |

A separate read-only reviewer inspected the task changes, RED/GREEN evidence,
provider reads and tool boundaries for both completed turns and found no blocker.
There was no corrective controller intervention; the second message introduced
the separate offline task. Workers did not delegate. Raw conversations, machine
paths and installation receipts remain private.

This is observed installation, conversation-catalog discovery and use on an
existing desktop profile, using the published fictional fixtures again. It is not
a held-out benchmark, GUI-picker test, clean-machine installation, human newcomer
study or broad behavioral certification. `behavioral_status` remains
`not_certified`. This reporting-only change leaves the tested workflow, provider
profile, adaptation and runtime bytes unchanged.

本轮已验证真实 macOS 安装、App 新会话技能目录发现、按名称加载及实际任务使用。
维护接口验收为 6/6，离线任务产物检查为 2/2，两项均另经独立过程审查。
复用了公开虚构样例，不是保留测试集；GUI 选择器、干净机器、真人新手体验及其他客户端
行为仍未验证。原始对话和本机回执不公开，不能将这些结果写成整体行为认证。

## Behavior evidence / 行为证据

The [scenario definitions](../evals/scenarios.md), [selection scenarios](../evals/github-selection.md), and [fictional walkthroughs](examples/new-project.md) separate acceptance criteria from observed results. Public reports may contain the declared synthetic inputs, commands, tool versions, acceptance assertions, and aggregate outcomes generated for those inputs. Expected output alone is not an executed result.

场景定义与虚构演练区分验收条件和实际结果。公开报告可包括专门构造的合成输入、命令、工具版本、验收断言及其汇总结果；预期输出不能冒充实测。

Do not attach local agent transcripts, machine receipts, private workspaces, real-case summaries, or anonymized rewrites. A defect report must be recreated with unrelated fictional data. Public evidence must not claim automatic App discovery, a complete workflow, beginner reliability, or comparative superiority beyond what was actually observed.

不附带本机 Agent 对话、机器回执、私有工作区、真实案例摘要或匿名改写。问题需用无关虚构数据独立复现，结论不得超出实际观测。
