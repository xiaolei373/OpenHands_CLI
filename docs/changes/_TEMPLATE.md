<!--
变更记录模板。复制本文件为 docs/changes/YYYY-MM-DD-<简短英文slug>.md 后填写。
只对"非平凡改动"（改逻辑/依赖/spec/接口/行为）建记录；纯格式化、typo、注释可跳过。
一次逻辑改动一个文件；文件名里的日期用改动当天的绝对日期。
-->

# <一句话标题：本次改动做了什么>

- 日期: YYYY-MM-DD
- 作者: <name>
- 关联: <iCafe 卡片 如 amea-269 / commit SHA / 评审链接，可多个>
- 类型: feature | fix | refactor | chore | docs | perf | build

## 背景（为什么改）
<触发这次改动的问题、需求或约束。写清"不改会怎样"，便于日后判断是否仍需要。>

## 改动内容与影响范围
- 改动的文件/模块：<路径列表>
- 行为变化：<对外可见行为、接口、数据格式是否变化；有无破坏性变更>
- 波及范围：<还有哪些模块/调用方受影响；是否影响 vendored SDK>

## 如何验证
<实际跑过的命令 + 结果，不是"应该能过"。至少覆盖：>
- [ ] `make lint`
- [ ] `make test`（或列出具体跑的用例）
- [ ] 若涉及打包/二进制/vendor/mcp/entrypoint：`./build.sh` + `./dist/openhands --help` + 一个真实任务跑通（无 ModuleNotFoundError / 缺数据文件）
- 结果摘要：<关键输出/结论>

## 是否需要改 spec（openhands-cli.spec）
- [ ] 不需要 —— 原因：<未新增运行时依赖/数据文件/动态导入>
- [ ] 需要 —— 改了什么：<hiddenimports / datas / copy_metadata / pathex ...>，并已按上面"如何验证"重打二进制确认

## 风险与回滚
<已知风险、兼容性影响（如 glibc）、如何回滚（revert 哪个 commit）。>
