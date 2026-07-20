# 建立变更工作流与变更记录机制

- 日期: 2026-07-20
- 作者: zhaolei36
- 关联: amea-269 [Story]【OpenHands】CLI精简
- 类型: docs

## 背景（为什么改）
之前每次改代码（尤其改 vendored SDK / `openhands-cli.spec`）缺少统一的自查与留痕机制，
容易出现"改完不知道要不要重打二进制、要不要改 spec、几个月后想不起当初为什么改"。
需要一套固定流程，让每次非平凡改动都依次核对：背景、影响范围、如何验证、是否需要改 spec，
并留下可回溯的记录。

## 改动内容与影响范围
- 改动的文件/模块：
  - `AGENTS.md`：新增 “Change Workflow (MUST)” 一节，规定四步自查 + 记录要求。
  - `docs/changes/_TEMPLATE.md`：变更记录模板。
  - `docs/changes/README.md`：目录约定说明。
  - `docs/changes/2026-07-20-add-change-workflow.md`：本记录（首条，兼作示例）。
- 行为变化：仅文档/流程，无代码行为变化，无接口/数据格式变化。
- 波及范围：影响后续所有贡献者与 AI 的协作方式；不涉及 `vendor/` 运行时代码。

## 如何验证
- [x] 纯文档改动，无需 `make lint` / `make test` / 打包验证。
- 结果摘要：Markdown 内容与链接（`docs/changes/_TEMPLATE.md`、`docs/changes/README.md`）核对无误。

## 是否需要改 spec（openhands-cli.spec）
- [x] 不需要 —— 仅新增文档，未新增运行时依赖/数据文件/动态导入。

## 风险与回滚
无功能风险。如需撤销，revert 本次提交即可（删除 `docs/changes/` 与 AGENTS.md 中新增小节）。
