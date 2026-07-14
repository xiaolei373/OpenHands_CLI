# CLI 精简改造记录（Headless-only）

- 整理日期：2026-07-14
- 适用版本：OpenHands CLI 1.15.1
- 目标：只保留 `openhands --headless` 场景（容器内自动解决任务），移除交互式 TUI、`--json` 及其它子命令，代码尽量精简
- git 基线：`4dbefa5 baseline: slimmed headless-only CLI`（改造前无 git，故无法生成改造前后的 diff，本文档为唯一的文字回溯依据）

---

## 1. 最终形态

### 运行方式
```bash
openhands --task "任务描述"
openhands --file task.md
openhands --resume <conversation-id> --task "继续"
openhands --llm-approve --task "..."
openhands --override-with-envs --task "..."   # 用 LLM_API_KEY/LLM_BASE_URL/LLM_MODEL 覆盖
```

### 调用链（已彻底脱离 Textual）
```
entrypoint.main()
  → 解析参数（--task/-f/--resume/--yolo/--llm-approve/--override-with-envs）
  → headless_runner.run_headless()
      → setup_conversation(policy=NeverConfirm, visualizer=DefaultConversationVisualizer)
      → conversation.send_message(task)
      → conversation.run()
      → 打印 CONVERSATION SUMMARY + conversation_id
```

### 现存文件（openhands_cli/，共 15 个 .py，约 1818 行）
- 核心：`entrypoint.py`、`headless_runner.py`、`setup.py`、`utils.py`
- 加载/配置：`stores/agent_store.py`、`stores/cli_settings.py`、`stores/__init__.py`、`locations.py`
- 其它：`mcp/mcp_utils.py`（MCP 配置，保留）、`shared/conversation_summary.py`、`shared/__init__.py`
- 参数：`argparsers/main_parser.py`、`argparsers/util.py`
- 包标记：`__init__.py`

---

## 2. 删除清单

### 2.1 整目录删除
- `openhands_cli/tui/`：整个 Textual UI（textual_app、widgets、panels、modals、core 下所有 controller/runner/state/conversation_manager、richlog_visualizer、serve.py 等）
- `openhands_cli/acp_impl/`：ACP（Agent-Client Protocol）服务端实现，对应 `acp` 子命令
- `openhands_cli/cloud/`：OpenHands Cloud 会话，对应 `cloud` 子命令
- `openhands_cli/auth/`：登录/登出、device flow、token 存储，对应 `login`/`logout` 子命令
- `openhands_cli/conversations/`：CLI 侧会话列表/查看/本地&云存储（resume 改由 SDK 持久化实现，无需此包）
- `openhands_cli/user_actions/`：`UserConfirmation` 枚举，仅被已删的 conversation_runner 使用

### 2.2 单文件删除
- `openhands_cli/gui_launcher.py`：`serve` 子命令（Docker GUI 服务）
- `openhands_cli/tui/serve.py`：`web` 子命令（textual-serve 浏览器版）
- `openhands_cli/terminal_compat.py`：交互式 TTY 兼容性检测
- `openhands_cli/version_check.py`：无任何引用
- `openhands_cli/deprecated_utils.py`：仅提供 `conversation_has_delegate_tool`（旧 DelegateTool 会话兼容），确认不涉及 DelegateTool 后删除
- `openhands_cli/theme.py`：Textual 主题对象（`import textual.theme.Theme`），仅用于控制台着色，已内联为 rich 十六进制颜色
- `openhands_cli/mcp/mcp_commands.py`、`openhands_cli/mcp/mcp_display_utils.py`：`mcp` 子命令的命令处理与展示（保留 `mcp_utils.py`，agent_store 依赖）
- `openhands_cli/shared/slash_commands.py`：斜杠命令解析（仅交互式 TUI 使用）
- `openhands_cli/shared/delegate_formatter.py`：仅被 tui 的 richlog_visualizer 使用
- `openhands_cli/argparsers/` 下 7 个子 parser：`acp_parser.py`、`auth_parser.py`、`cloud_parser.py`、`serve_parser.py`、`web_parser.py`、`view_parser.py`、`mcp_parser.py`

---

## 3. 新增文件

### `openhands_cli/headless_runner.py`（约 93 行）
最小 headless 执行器，直接驱动 SDK：
- `_select_confirmation_policy(llm_approve)`：默认 `NeverConfirm`（自动批准）；`--llm-approve` 用 `ConfirmRisky(threshold=HIGH)`
- `run_headless(task, resume_id, llm_approve, env_overrides_enabled, critic_disabled=True)`：
  - 新会话生成 UUID，resume 时用传入 ID（SDK 自动加载持久化状态）
  - `setup_conversation(visualizer=DefaultConversationVisualizer)` → 事件直接流式打印到 stdout（容器日志友好）
  - `send_message` → `run()` → `_print_summary`
- 无 Textual、无 asyncio 事件循环、无 reactive state

---

## 4. 改造清单（文件级）

### `openhands_cli/entrypoint.py`（整体重写）
- 删除所有子命令分支（serve/web/acp/cloud/login/logout/mcp/view）与 `handle_resume_logic` 的列表展示逻辑
- 仅保留 headless：解析参数 → 校验 task/file → `run_headless()` → 打印会话 ID 与 resume 提示
- 移除 `from openhands_cli.theme import OPENHANDS_THEME`，着色改用 rich 十六进制颜色
  （`#ffe165` 成功、`#277dff` 强调、`#ffffff` 普通、`#ff6b6b` 错误）
- 异常处理保留 `MissingEnvironmentVariablesError`、`MissingAgentSpec`

### `openhands_cli/argparsers/main_parser.py`（重写）
- 删除全部 `add_subparsers` 及 7 个子 parser 引用
- 仅保留：`--version/-v`、`--task/-t`、`--file/-f`、`--resume`、`--always-approve/--yolo`、`--llm-approve`、`--override-with-envs`

### `openhands_cli/argparsers/util.py`
- 删除 `add_resume_args`（含已废弃的 `--last`/交互式列表）
- 保留 `add_confirmation_mode_args`、`add_env_override_args`

### `openhands_cli/setup.py`
- 移除 `from openhands_cli.tui.widgets.richlog_visualizer import ConversationVisualizer`
- `setup_conversation` 的 `visualizer` 形参类型改为
  `ConversationVisualizerBase | type[ConversationVisualizerBase] | None`
- 其余逻辑不变（agent 加载、hooks、LLMSecurityAnalyzer、确认策略）

### `openhands_cli/stores/agent_store.py`
- 移除 `from openhands_cli.deprecated_utils import conversation_has_delegate_tool`
- 工具解析方法去掉 DelegateTool 探测分支：有持久化工具则用，否则用默认 CLI 工具集

### `openhands_cli/utils.py`
- 删除无用函数：`abbreviate_number`、`format_cost`（状态栏用）、
  `extract_text_from_message_content`（斜杠命令用）、`json_callback`（`--json` 用）
- `get_default_cli_tools()` 去掉 `use_delegate_tool` 参数，固定使用 `TaskToolSet`
- 移除相关 import：`json`、`SystemPromptEvent`、`Event`、`TextContent`、`ImageContent`、`DelegateTool`
- 保留 `get_default_cli_agent`、`get_default_cli_tools`、`get_llm_metadata`、
  `get_os_description`、`should_set_litellm_extra_body`、`create_seeded_instructions_from_args`

### `openhands_cli/shared/__init__.py`
- 去掉 `parse_slash_command` 导出，仅保留 `extract_conversation_summary`

### `openhands_cli/headless_runner.py`
- 着色使用 rich 十六进制颜色（与 entrypoint 一致），未依赖 theme

### `pyproject.toml`
- `[project.scripts]` 删除 `openhands-acp = "openhands_cli.acp:main"`，仅保留 `openhands = "openhands_cli.entrypoint:main"`

---

## 5. 验证记录
- import：`entrypoint`/`headless_runner`/`setup`/`stores` 及 `create_main_parser()` 均正常
- lint：`ruff check openhands_cli/` 全部通过
- `--help` 与「缺少 task/file 报错」行为正确
- 端到端（真实 LLM，`openai/verl`，`--override-with-envs`）：
  任务「创建 hello.txt」成功执行 → 调用 file_editor 写文件 → 事件流式输出 →
  打印 SUMMARY + Conversation ID，退出码 0

---

## 6. 尚未处理 / 可选后续
- `mcp/mcp_utils.py`（约 411 行）：若放弃 MCP 工具配置，可删该文件并去掉 agent_store 中 `list_enabled_servers` 调用，CLI 可再降约 400 行
- `pyproject.toml` 依赖：`textual`、`textual-serve`、`textual-autocomplete`、`pytest-textual-snapshot`、`streamingjson`、`pyperclip` 等已无用，可移除以缩小安装体积
- 测试：`tests/`、`tui_e2e/`、`tests/snapshots/` 大量用例引用已删模块，需删除/重写；建议为 `headless_runner` 补最小单测

---

## 7. 如何回溯
- 本次改造前无 git，无法生成改造前后 diff；如需与官方原版对比，请另外下载 OpenHands CLI 1.15.1 源码做外部 diff
- 从基线 `4dbefa5` 之后的改动均可用 `git diff` / `git log` 查看
