"""dtJiraMCPServer - MCP Server for Jira Cloud and JSM Cloud administration."""

from pathlib import Path

__author__ = "Matthew Westwood-Hill"

_pkg_dir = Path(__file__).parent

_version_file = _pkg_dir / "_version.txt"
__version__ = _version_file.read_text(encoding="utf-8").strip() if _version_file.exists() else "0.0.0"

_short_name_file = _pkg_dir / "_short_name.txt"
__short_name__ = (
    _short_name_file.read_text(encoding="utf-8").strip() if _short_name_file.exists() else "dtUnknown"
)

_description_file = _pkg_dir / "_description.txt"
__description__ = (
    _description_file.read_text(encoding="utf-8").strip()
    if _description_file.exists()
    else "dtUnknown"
)

_full_name_file = _pkg_dir / "_full_name.txt"
__full_name__ = (
    _full_name_file.read_text(encoding="utf-8").strip() if _full_name_file.exists() else "dtUnknown"
)
