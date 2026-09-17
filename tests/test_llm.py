from __future__ import annotations

import os
import sys
from pathlib import Path
from subprocess import CompletedProcess
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "quanta_agents" not in sys.modules:
    package_stub = ModuleType("quanta_agents")
    package_stub.__path__ = [str(SRC_DIR / "quanta_agents")]  # type: ignore[attr-defined]
    sys.modules["quanta_agents"] = package_stub

from quanta_agents.llm import LLMClient


class CodexExecLLMClientTest(TestCase):
    @patch("quanta_agents.llm.OpenAI")
    def test_api_provider_remains_available_with_per_call_model(self, openai_mock) -> None:
        openai_mock.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="API结果"))]
        )
        env = {
            "QUANTA_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://example.invalid/v1",
            "OPENAI_MODEL": "default-api-model",
        }

        with patch.dict(os.environ, env, clear=False):
            client = LLMClient()
            result = client.complete(
                "系统",
                "用户",
                role="strategy",
                model="request-api-model",
            )

        self.assertEqual(result, "API结果")
        openai_mock.assert_called_once_with(
            api_key="test-key",
            base_url="https://example.invalid/v1",
        )
        create_kwargs = openai_mock.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(create_kwargs["model"], "request-api-model")

    @patch("quanta_agents.llm.subprocess.run")
    @patch("quanta_agents.llm.shutil.which", return_value=r"C:\tools\codex.cmd")
    def test_complete_uses_sol_ultra_and_stdin(self, _which, run_mock) -> None:
        run_mock.return_value = CompletedProcess([], 0, stdout="模型结果\n", stderr="")
        env = {
            "QUANTA_LLM_PROVIDER": "codex_exec",
            "CODEX_EXEC_MODEL": "gpt-5.6-sol",
            "CODEX_EXEC_REASONING_EFFORT": "ultra",
            "CODEX_EXEC_MULTI_AGENT": "false",
            "OPENAI_API_KEY": "must-not-reach-child",
            "OPENAI_BASE_URL": "https://example.invalid",
            "OPENAI_MODEL": "deepseek-chat",
        }

        with patch.dict(os.environ, env, clear=False):
            client = LLMClient()
            result = client.complete("系统说明", "用户问题")

        self.assertEqual(result, "模型结果")
        command = run_mock.call_args.args[0]
        kwargs = run_mock.call_args.kwargs
        self.assertIn("gpt-5.6-sol", command)
        self.assertIn('model_reasoning_effort="ultra"', command)
        self.assertNotIn("multi_agent", command)
        self.assertIn("read-only", command)
        self.assertEqual(command[-1], "-")
        self.assertIn("系统说明", kwargs["input"])
        self.assertIn("用户问题", kwargs["input"])
        self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
        self.assertNotIn("OPENAI_BASE_URL", kwargs["env"])
        self.assertNotIn("OPENAI_MODEL", kwargs["env"])

    @patch("quanta_agents.llm.subprocess.run")
    @patch("quanta_agents.llm.shutil.which", return_value=r"C:\tools\codex.cmd")
    def test_complete_accepts_role_specific_codex_settings(self, _which, run_mock) -> None:
        run_mock.return_value = CompletedProcess([], 0, stdout="策略结果\n", stderr="")
        env = {
            "QUANTA_LLM_PROVIDER": "codex_exec",
            "CODEX_EXEC_MODEL": "gpt-5.6-sol",
            "CODEX_EXEC_REASONING_EFFORT": "high",
            "CODEX_EXEC_MULTI_AGENT": "false",
        }

        with patch.dict(os.environ, env, clear=False):
            client = LLMClient()
            result = client.complete_messages(
                [{"role": "user", "content": "生成策略"}],
                role="strategy",
                model="gpt-5.6-sol",
                reasoning_effort="ultra",
                multi_agent=True,
            )

        self.assertEqual(result, "策略结果")
        command = run_mock.call_args.args[0]
        self.assertIn("gpt-5.6-sol", command)
        self.assertIn('model_reasoning_effort="ultra"', command)
        self.assertIn("multi_agent", command)

    @patch("quanta_agents.llm.subprocess.run")
    @patch("quanta_agents.llm.shutil.which", return_value=r"C:\tools\codex.cmd")
    def test_role_environment_overrides_codex_defaults(self, _which, run_mock) -> None:
        run_mock.return_value = CompletedProcess([], 0, stdout="角色结果\n", stderr="")
        env = {
            "QUANTA_LLM_PROVIDER": "codex_exec",
            "CODEX_EXEC_MODEL": "default-model",
            "CODEX_EXEC_REASONING_EFFORT": "medium",
            "CODEX_EXEC_MULTI_AGENT": "false",
            "CODEX_EXEC_STRATEGY_MODEL": "strategy-model",
            "CODEX_EXEC_STRATEGY_REASONING_EFFORT": "xhigh",
            "CODEX_EXEC_STRATEGY_MULTI_AGENT": "true",
        }

        with patch.dict(os.environ, env, clear=False):
            client = LLMClient()
            client.complete("系统", "用户", role="strategy")

        command = run_mock.call_args.args[0]
        self.assertIn("strategy-model", command)
        self.assertIn('model_reasoning_effort="xhigh"', command)
        self.assertIn("multi_agent", command)

    @patch("quanta_agents.llm.shutil.which", return_value=r"C:\tools\codex.cmd")
    def test_tool_request_runs_python_handler_then_returns_final_text(self, _which) -> None:
        env = {
            "QUANTA_LLM_PROVIDER": "codex_exec",
            "CODEX_EXEC_MODEL": "gpt-5.6-sol",
            "CODEX_EXEC_REASONING_EFFORT": "ultra",
        }
        first = (
            '{"action":"call_tools","tool_calls":['
            '{"name":"get_dataset_schema","arguments_json":'
            '"{\\"table_key\\":\\"stock_kline_daily_qfq\\"}"}],"final_text":""}'
        )
        second = (
            '{"action":"final","tool_calls":[],"final_text":'
            '"{\\"hypothesis\\":\\"test\\"}"}'
        )

        with patch.dict(os.environ, env, clear=False):
            client = LLMClient()
            with patch.object(client, "_complete_codex_messages", side_effect=[first, second]):
                text, events = client.complete_with_tools(
                    system_prompt="system",
                    user_prompt="user",
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "get_dataset_schema",
                                "parameters": {"type": "object"},
                            },
                        }
                    ],
                    tool_handlers={
                        "get_dataset_schema": lambda table_key: {
                            "passed": True,
                            "table_key": table_key,
                        }
                    },
                    require_json_object=True,
                )

        self.assertEqual(text, '{"hypothesis":"test"}')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tool_name"], "get_dataset_schema")
        self.assertEqual(
            events[0]["arguments"],
            {"table_key": "stock_kline_daily_qfq"},
        )
        self.assertTrue(events[0]["result"]["passed"])
