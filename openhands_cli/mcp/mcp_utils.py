"""MCP configuration loading.

Reads the persisted MCP server configuration and exposes the servers that are
currently enabled so they can be attached to the agent at runtime.
"""

from pathlib import Path

from fastmcp.mcp_config import MCPConfig, RemoteMCPServer, StdioMCPServer
from pydantic import ValidationError as PydanticValidationError


def _get_mcp_config_path() -> Path:
    """Get the MCP configuration file path.

    This function dynamically resolves the path to ensure it works
    correctly when PERSISTENCE_DIR is patched in tests.
    """
    # Import the module and get the current value to support patching
    import openhands_cli.locations as locations

    return Path(locations.get_persistence_dir()) / locations.MCP_CONFIG_FILE


class MCPConfigurationError(Exception):
    """Exception raised for MCP configuration errors."""

    pass


def load_mcp_config() -> MCPConfig:
    """Load the MCP configuration from file.

    Returns:
        The MCPConfig object, or empty config if file doesn't exist.

    Raises:
        MCPConfigurationError: If the configuration file is invalid.
    """
    config_path = _get_mcp_config_path()
    if not config_path.exists():
        # Return empty config with mcpServers structure
        return MCPConfig.from_dict({"mcpServers": {}})

    try:
        return MCPConfig.from_file(config_path)
    except (ValueError, PydanticValidationError) as e:
        # Re-raise as MCPConfigurationError for consistency
        raise MCPConfigurationError(f"Invalid MCP configuration file: {e}") from e
    except Exception as e:
        raise MCPConfigurationError(f"Error reading config file: {e}") from e


def list_enabled_servers() -> dict[str, StdioMCPServer | RemoteMCPServer]:
    """List only enabled MCP servers.

    Returns:
        Dictionary of enabled server objects keyed by name
    """
    config = load_mcp_config()
    enabled_servers = {}

    for name, server in config.mcpServers.items():
        server_dict = server.model_dump()
        # Default to True if enabled field is not present (backwards compatibility)
        if server_dict.get("enabled", True):
            enabled_servers[name] = server

    return enabled_servers
