"""
DSN Discovery - Windows-specific ODBC DSN discovery for Zen databases.

Discovers Zen/Pervasive ODBC DSNs from Windows registry.
Separated to allow clean platform-specific imports.
"""

import platform
from typing import Dict, Optional, Any

if platform.system() != 'Windows':
    raise ImportError("DSN discovery requires Windows")

import winreg
import pyodbc


def discover_zen_dsns() -> Dict[str, Dict[str, Any]]:
    """
    Auto-discover Zen/Pervasive ODBC DSNs from Windows.

    Returns:
        dict of DSN name -> details (driver, database, server, etc.)
    """
    zen_dsns = {}

    try:
        # Get all ODBC data sources
        all_dsns = pyodbc.dataSources()

        # Filter for Zen/Pervasive DSNs
        for dsn_name, driver in all_dsns.items():
            if 'Pervasive' in driver or 'Zen' in driver or 'PSQL' in driver:
                dsn_info = {
                    'name': dsn_name,
                    'driver': driver,
                    'type': 'dsn'
                }

                # Try to get additional details from registry
                details = get_dsn_registry_details(dsn_name)
                if details:
                    dsn_info.update(details)

                zen_dsns[dsn_name] = dsn_info
    except Exception:
        pass  # Silently fail if discovery doesn't work

    return zen_dsns


def get_dsn_registry_details(dsn_name: str) -> Optional[Dict[str, str]]:
    """
    Get DSN connection details from Windows registry.

    Args:
        dsn_name: Name of the ODBC DSN

    Returns:
        dict with database, server, port, description, transport
        or None if not found
    """
    # Registry paths to check (64-bit and 32-bit)
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\ODBC\ODBC.INI'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\ODBC\ODBC.INI'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\ODBC\ODBC.INI'),
    ]

    for hkey, base_path in registry_paths:
        try:
            key_path = base_path + '\\' + dsn_name
            key = winreg.OpenKey(hkey, key_path)
            details = {}
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    # Map registry keys to friendly names
                    if name == 'DBQ':
                        details['database'] = value
                    elif name == 'ServerName':
                        details['server'] = value
                    elif name == 'TCPPort':
                        details['port'] = value
                    elif name == 'Description':
                        details['description'] = value
                    elif name == 'TransportHint':
                        details['transport'] = value
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
            if details:
                return details
        except FileNotFoundError:
            continue
        except Exception:
            continue

    return None


def auto_select_default_dsn() -> Optional[str]:
    """
    Auto-select the best default DSN.

    Priority:
    1. 'demodata' if available
    2. First available Zen DSN
    3. None if no DSNs found
    """
    zen_dsns = discover_zen_dsns()

    if not zen_dsns:
        return None

    # Prefer 'demodata' if available
    if 'demodata' in zen_dsns:
        return 'demodata'

    # Otherwise return first available
    return next(iter(zen_dsns.keys()))


def get_dsn_connection_string(dsn_name: str) -> str:
    """Get connection string for a DSN (simple DSN= format)."""
    return f"DSN={dsn_name}"


def list_all_dsns() -> Dict[str, Dict[str, Any]]:
    """
    List all discovered Zen DSNs with full details.

    Returns:
        dict suitable for JSON serialization
    """
    dsns = discover_zen_dsns()
    return {
        "dsns": list(dsns.values()),
        "count": len(dsns),
        "default": auto_select_default_dsn()
    }
