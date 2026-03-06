"""
ZenConfiguration - Hybrid configuration manager for Actian Zen MCP Server.

Priority-based configuration loading:
1. CLI arguments (--conf-file or --dsn)
2. Environment variables (ZEN_DSN, ZEN_CONN_STRING)
3. Default config file (zen_config.json)
4. Auto-discovery from Windows registry
5. Fail with helpful error

Based on design from: docs/configuration-differences.md
"""

import os
import json
import argparse
import platform
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ConnectionConfig:
    """Validated connection configuration."""
    conn_string: str
    dsn_name: Optional[str] = None
    source: str = "unknown"  # "cli", "env", "config_file", "auto_discovery"


class ZenConfiguration:
    """
    Unified configuration manager with multiple sources.

    Priority:
    1. CLI arguments (--conf-file or --dsn)
    2. Environment variables (ZEN_DSN, ZEN_CONN_STRING)
    3. Default config file (if exists)
    4. Auto-discovery from Windows registry
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory to look for config files.
                        Defaults to module directory.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent
        self.config_dir = config_dir
        self.default_config_file = config_dir / "zen_config.json"
        self._config: Optional[ConnectionConfig] = None

    def load_from_cli(self, args: argparse.Namespace) -> ConnectionConfig:
        """
        Load configuration from CLI arguments.

        Args:
            args: Parsed command line arguments

        Returns:
            ConnectionConfig with validated connection string
        """
        # Priority 1: Explicit config file
        if hasattr(args, 'conf_file') and args.conf_file:
            return self._load_from_json(args.conf_file, source="cli")

        # Priority 2: Explicit DSN
        if hasattr(args, 'dsn') and args.dsn:
            return ConnectionConfig(
                conn_string=f"DSN={args.dsn}",
                dsn_name=args.dsn,
                source="cli"
            )

        # Priority 3: Environment variables
        config = self._load_from_env()
        if config:
            return config

        # Priority 4: Default config file (if exists)
        if self.default_config_file.exists():
            return self._load_from_json(self.default_config_file, source="config_file")

        # Priority 5: Auto-discovery (Windows only)
        return self._auto_discover()

    def _load_from_env(self) -> Optional[ConnectionConfig]:
        """Load configuration from environment variables."""
        if os.environ.get("ZEN_CONN_STRING"):
            return ConnectionConfig(
                conn_string=os.environ["ZEN_CONN_STRING"],
                source="env"
            )

        if os.environ.get("ZEN_DSN"):
            dsn = os.environ["ZEN_DSN"]
            return ConnectionConfig(
                conn_string=f"DSN={dsn}",
                dsn_name=dsn,
                source="env"
            )

        return None

    def _load_from_json(self, config_path: str | Path, source: str) -> ConnectionConfig:
        """
        Load configuration from JSON file.

        Supports two formats:
        1. New format: {"connection": {"type": "dsn", "dsn": "demodata"}}
        2. ActianMCP format: {"conn_string": "DSN=demodata"}
        """
        path = Path(config_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, 'r') as f:
            config = json.load(f)

        # Support new format
        if "connection" in config:
            conn = config["connection"]
            if conn.get("type") == "dsn":
                conn_str = f"DSN={conn['dsn']}"
                # Add credentials if provided
                if conn.get("uid"):
                    conn_str += f";Uid={conn['uid']}"
                if conn.get("pwd"):
                    conn_str += f";Pwd={conn['pwd']}"
                return ConnectionConfig(
                    conn_string=conn_str,
                    dsn_name=conn["dsn"],
                    source=source
                )
            elif conn.get("type") == "driver" or "conn_string" in conn:
                return ConnectionConfig(
                    conn_string=conn.get("conn_string", conn.get("connection_string")),
                    source=source
                )

        # Backward compatible with ActianMCP format
        if "conn_string" in config:
            return ConnectionConfig(
                conn_string=config["conn_string"],
                source=source
            )

        raise ValueError(
            f"Invalid config file: {path}. "
            "Must contain 'conn_string' or 'connection' key."
        )

    def _auto_discover(self) -> ConnectionConfig:
        """Auto-discover DSN from Windows registry."""
        if platform.system() != 'Windows':
            raise RuntimeError(
                "Auto-discovery requires Windows. Options:\n"
                "  1. Use --conf-file with JSON config\n"
                "  2. Use --dsn with DSN name\n"
                "  3. Set ZEN_DSN or ZEN_CONN_STRING environment variable"
            )

        try:
            from .dsn_discovery import discover_zen_dsns, auto_select_default_dsn

            dsns = discover_zen_dsns()
            if not dsns:
                raise RuntimeError(
                    "No Zen DSNs found in Windows registry. Options:\n"
                    "  1. Use --conf-file with JSON config\n"
                    "  2. Use --dsn with DSN name\n"
                    "  3. Set ZEN_DSN or ZEN_CONN_STRING environment variable\n"
                    "  4. Create a Zen ODBC DSN in Windows ODBC Administrator"
                )

            dsn = auto_select_default_dsn()
            return ConnectionConfig(
                conn_string=f"DSN={dsn}",
                dsn_name=dsn,
                source="auto_discovery"
            )
        except ImportError as e:
            raise RuntimeError(
                f"Auto-discovery not available: {e}. "
                "Use --conf-file, --dsn, or environment variables."
            )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments with merged options."""
    parser = argparse.ArgumentParser(
        description="Actian Zen MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Priority:
  1. --conf-file (JSON config file)
  2. --dsn (direct DSN name)
  3. ZEN_CONN_STRING or ZEN_DSN environment variables
  4. zen_config.json in module directory
  5. Auto-discovery from Windows ODBC registry

Examples:
  actian-zen                          # Auto-discover DSN
  actian-zen --dsn demodata           # Use specific DSN
  actian-zen --conf-file ./config.json # Use JSON config
  ZEN_DSN=demodata actian-zen         # Via environment
        """
    )

    parser.add_argument(
        "--conf-file",
        help="Path to JSON configuration file"
    )
    parser.add_argument(
        "--dsn",
        help="ODBC DSN name to connect to"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="MCP transport: stdio, http, or sse (default: stdio)"
    )
    parser.add_argument(
        "--readonly",
        action="store_true",
        default=False,
        help="Run in read-only mode: 6 tools (no DDL, batch, transaction)"
    )

    return parser.parse_args()
