"""Unit tests for MCP configuration loading."""

import json

import pytest

from openhands_cli.mcp.mcp_utils import (
    MCPConfigurationError,
    list_enabled_servers,
    load_mcp_config,
)


# temp_config_path fixture is provided by tests/conftest.py


def _write_config(temp_config_path, servers: dict) -> None:
    """Write an mcp.json config file with the given servers mapping."""
    temp_config_path.write_text(json.dumps({"mcpServers": servers}))


class TestLoadMCPConfig:
    """Test cases for load_mcp_config."""

    def test_load_config_nonexistent_file(self, temp_config_path):
        """Test loading config when file doesn't exist."""
        config = load_mcp_config()
        assert config.to_dict() == {"mcpServers": {}}

    def test_load_config_valid_file(self, temp_config_path):
        """Test loading config from valid JSON file."""
        _write_config(
            temp_config_path,
            {"test_server": {"command": "test", "transport": "stdio"}},
        )

        config = load_mcp_config()
        servers_dict = config.to_dict()["mcpServers"]
        assert "test_server" in servers_dict
        assert servers_dict["test_server"]["command"] == "test"
        assert servers_dict["test_server"]["transport"] == "stdio"

    def test_load_config_missing_mcp_servers_key(self, temp_config_path):
        """Test loading config that's missing mcpServers key."""
        temp_config_path.write_text(json.dumps({"other_key": "value"}))

        config = load_mcp_config()
        config_dict = config.to_dict()
        assert "mcpServers" in config_dict
        assert config_dict["mcpServers"] == {}

    def test_load_config_invalid_json(self, temp_config_path):
        """Test loading config with invalid JSON."""
        temp_config_path.write_text("invalid json content")

        with pytest.raises(MCPConfigurationError):
            load_mcp_config()


class TestListEnabledServers:
    """Test cases for list_enabled_servers."""

    def test_list_enabled_servers_empty(self, temp_config_path):
        """Test listing enabled servers when none exist."""
        assert list_enabled_servers() == {}

    def test_list_enabled_servers_all_enabled(self, temp_config_path):
        """Test listing enabled servers when all are enabled."""
        _write_config(
            temp_config_path,
            {
                "test1": {
                    "url": "https://example1.com",
                    "transport": "http",
                    "enabled": True,
                },
                "test2": {
                    "url": "https://example2.com",
                    "transport": "http",
                    "enabled": True,
                },
            },
        )

        enabled_servers = list_enabled_servers()
        assert set(enabled_servers) == {"test1", "test2"}

    def test_list_enabled_servers_mixed(self, temp_config_path):
        """Test listing enabled servers when some are disabled."""
        _write_config(
            temp_config_path,
            {
                "enabled1": {
                    "url": "https://example1.com",
                    "transport": "http",
                    "enabled": True,
                },
                "disabled": {
                    "url": "https://example2.com",
                    "transport": "http",
                    "enabled": False,
                },
                "enabled2": {
                    "url": "https://example3.com",
                    "transport": "http",
                    "enabled": True,
                },
            },
        )

        enabled_servers = list_enabled_servers()
        assert set(enabled_servers) == {"enabled1", "enabled2"}

    def test_list_enabled_servers_all_disabled(self, temp_config_path):
        """Test listing enabled servers when all are disabled."""
        _write_config(
            temp_config_path,
            {
                "test1": {
                    "url": "https://example1.com",
                    "transport": "http",
                    "enabled": False,
                },
                "test2": {
                    "url": "https://example2.com",
                    "transport": "http",
                    "enabled": False,
                },
            },
        )

        assert list_enabled_servers() == {}

    def test_list_enabled_servers_defaults_to_enabled(self, temp_config_path):
        """Servers without an explicit enabled field default to enabled."""
        _write_config(
            temp_config_path,
            {"test": {"url": "https://example.com", "transport": "http"}},
        )

        assert set(list_enabled_servers()) == {"test"}
