# Contributing / 参与贡献

Focused defects, documentation improvements, and workflow changes backed by reproducible evidence are welcome. Read the [roadmap](ROADMAP.md), [installation contract](docs/installation.md), and [validation scope](docs/validation.md) first.

欢迎可复现的问题、范围明确的文档修正，以及有证据支持的流程改进。先了解路线图、安装约定与验证边界。

## Report an independent reproduction / 独立构造复现

Include the package version, provider revision, client/environment, expected and observed behavior, and exact reproduction steps. Use **newly invented fictional data unrelated to a real project**. State which checks actually ran and disclose incomplete or failed steps.

说明包版本、provider 提交、客户端与环境、预期与实际行为及复现步骤。**使用与真实项目无关、全新编写的虚构数据**，列明实际检查、失败与未完成项。

Do not upload private inputs, project files, task histories, local receipts, agent transcripts, personal paths, or real-case summaries. Removing names or rewriting a private incident does not make it an acceptable public fixture. Recreate the defect independently instead. Inspect your proposed files and commit metadata before publishing.

不要上传私有输入、项目文件、任务历史、本机回执、Agent 对话、个人路径或真实案例摘要。删去名字或改写私有经历不等于可以公开，应独立构造复现。发布前检查文件及提交元数据。

Use the GitHub-provided noreply address from your account settings for public commits if you do not want a personal email disclosed. Check both author and committer on the actual published commit; local configuration alone does not verify a remotely created commit's identity.

不希望公开个人邮箱时，使用账号设置提供的 GitHub noreply 地址；检查实际远端提交的作者与提交者，不能只检查本地配置。

For GitHub web operations and pull requests, enable the account's
[private email setting](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address).
Inspect platform-generated test-merge commits as well as authored commits;
repository-local Git configuration does not control their account identity.

GitHub 网页操作与 PR 还需开启账号邮箱隐私，并核对平台自动生成的测试合并提交；
仓库内的 Git 邮箱配置不能代替这项检查。

## Keep the workflow coherent / 保持流程一致

- Dumbcane owns orchestration; Superpowers provides engineering methods. Keep one controller and resolve methods through the selected physical provider.
- Preserve existing user decisions and project work. Do not add repeated approvals for already authorized routine steps.
- Keep missing dependencies, resource drift, required route decisions, and verification gaps explicit.
- Never grant a new action merely because a method, web page, or tool output asks for it. Task authorization and platform rules still apply.
- Describe the final behavior, reason, actual verification, and remaining limits in the pull request.

保持单一编排入口、适用决定和原有工作。方法文本或外部内容不能自行授权行动，PR 应说明实际变化、原因、验证及限制。

## Check changes / 验证改动

With Python 3.11+, from the repository root:

```sh
python3 -B scripts/check.py --package-root . --json
python3 -B -m unittest discover -s tests -v
```

Provider changes additionally require public provenance, a fixed revision, reviewed relevant resources and semantic differences, content verification, and scoped behavioral checks. Updating hashes just to suppress a failure is insufficient. Use `--provider-root` to check a public provider directory; see the [checker contract](docs/checker-contract.md).

涉及 provider 的改动还需公开来源、固定提交、相关资源及语义审查、内容核验与明确范围的行为验证，不能只改指纹消除失败。

Exercise installation changes using `scripts/manage.py` with `--home` pointing to a newly created temporary directory. Verify unknown-entry rejection, failure preservation, complete-combination rollback, and owned-entry removal. Do not test ownership behavior against a contributor's real installed skills.

安装变更应将 `--home` 指向新建临时目录，覆盖未知入口拒绝、失败保留、组合回滚和归属检查，不拿真实技能目录做破坏性测试。

For behavior fixes, verification must demonstrate the defect and corrected behavior on independent fictional inputs. Documentation-only changes can use targeted review and link checks. Do not weaken a useful failing assertion to obtain a passing result. Mark expected walkthroughs, actual tool results, native-agent observations, App discovery, and human usability separately.

行为修复须证明问题及纠正效果；文档按影响检查。不要削弱有效断言以制造通过，区分演练、工具实测、Agent 行为、App 发现和真人可用性。

## License / 许可

Verify rights and attribution for contributed material. Preserve the repository [MIT license](LICENSE) and [third-party notices](THIRD_PARTY.md). Provider source is separately downloaded with its upstream license intact; do not introduce private provider code or redistribute other material without applicable rights.

核实贡献内容的权利与署名，保留许可及第三方声明。provider 单独下载并保留上游许可，不加入私有方法源码或无权再分发的资料。
